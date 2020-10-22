import io
import logging
from pprint import pprint  # noqa
from datetime import datetime
from normality import stringify
from followthemoney import model

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox
from pdfminer.layout import LTImage, LTText, LTContainer
from pdfminer.jbig2 import JBIG2StreamReader, JBIG2StreamWriter
from pdfminer.image import ImageWriter, BMPWriter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdftypes import resolve1, PDFException
from pdfminer.pdfparser import PDFParser
from pdfminer.psparser import PSException
from pdfminer.pdfcolor import LITERAL_DEVICE_GRAY, LITERAL_DEVICE_RGB
from pdfminer.pdfdocument import PDFDocument

from ingestors.support.ocr import OCRSupport
from ingestors.support.xmp import XMPParser
from ingestors.support.convert import DocumentConvertSupport
from ingestors.exc import ProcessingException

log = logging.getLogger(__name__)


class PDFSupport(DocumentConvertSupport, OCRSupport):
    """Provides helpers for PDF file context extraction."""

    def load_image(self, image):
        (width, height) = image.srcsize
        fp = io.BytesIO()
        try:
            full_data = image.stream.get_data()
        except (ValueError, PDFException):
            full_data = image.stream.get_rawdata()

        # if ext == ".jpg":
        #     raw_data = image.stream.get_rawdata()
        #     if LITERAL_DEVICE_CMYK in image.colorspace:
        #         from PIL import Image
        #         from PIL import ImageChops

        #         ifp = BytesIO(raw_data)
        #         i = Image.open(ifp)
        #         i = ImageChops.invert(i)
        #         i = i.convert("RGB")
        #         i.save(fp, "JPEG")
        #     else:
        #         fp.write(raw_data)
        if ImageWriter.is_jbig2_image(image):
            print("IMAGE IS JBIG2")
            input_stream = io.BytesIO()
            input_stream.write(full_data)
            input_stream.seek(0)
            reader = JBIG2StreamReader(input_stream)
            segments = reader.get_segments()
            writer = JBIG2StreamWriter(fp)
            writer.write_file(segments)
            with open("out.jbig2", "wb") as fh:
                writer = JBIG2StreamWriter(fh)
                writer.write_file(segments)
        elif image.bits == 1:
            print("IMAGE IS BMP")
            bmp = BMPWriter(fp, 1, width, height)
            i = 0
            width = (width + 7) // 8
            for y in range(height):
                bmp.write_line(y, full_data[i : i + width])
                i += width
        elif image.bits == 8 and LITERAL_DEVICE_RGB in image.colorspace:
            print("IMAGE IS BMP RGB")
            bmp = BMPWriter(fp, 24, width, height)
            i = 0
            width = width * 3
            for y in range(height):
                bmp.write_line(y, full_data[i : i + width])
                i += width
        elif image.bits == 8 and LITERAL_DEVICE_GRAY in image.colorspace:
            print("IMAGE IS BMP GRAY")
            bmp = BMPWriter(fp, 8, width, height)
            i = 0
            for y in range(height):
                bmp.write_line(y, full_data[i : i + width])
                i += width
        else:
            print("IMAGE IS OTHER", image.bit)
            return full_data
        return fp.getvalue()

    def render_item(self, item, languages):
        if isinstance(item, LTContainer):
            for child in item:
                yield from self.render_item(child, languages)
        elif isinstance(item, LTText):
            yield item.get_text()
        if isinstance(item, LTTextBox):
            yield "\n"
        elif isinstance(item, LTImage):
            data = self.load_image(item)
            text = self.extract_ocr_text(data, languages=languages)
            if text is not None:
                yield text
            yield "\n"

    def extract_page(self, document, interpreter, page, device, page_no):
        languages = self.manager.context.get("languages")
        try:
            interpreter.process_page(page)
            layout = device.get_result()
            text = "".join(self.render_item(layout, languages))
        except (PSException, PDFException):
            log.exception("[%r] Error parsing page: %s", document, page_no)
            text = None

        entity = self.manager.make_entity("Page")
        entity.make_id(document.id, page_no)
        entity.set("document", document)
        entity.set("index", page_no)
        entity.add("bodyText", text)
        self.manager.apply_context(entity, document)
        self.manager.emit_entity(entity)
        self.manager.emit_text_fragment(document, text, entity.id)

    def parse_pdf_date(self, date):
        date = stringify(date)
        if date is None:
            return
        if date.startswith("D:"):
            date = date[2:]
        try:
            dt = datetime.strptime(date[:14], "%Y%m%d%H%M%S")
            return dt.isoformat()
        except ValueError:
            return

    def pdf_metadata(self, entity, doc):
        #     entity.add("messageId", xmp["xmpmm"].get("documentid"))
        #         entity.add("title", xmp["dc"].get("title"))
        #         entity.add("generator", xmp["pdf"].get("producer"))
        #         entity.add("language", xmp["dc"].get("language"))
        #         entity.add("authoredAt", xmp["xmp"].get("createdate"))
        #         entity.add("modifiedAt", xmp["xmp"].get("modifydate"))
        #     except Exception as ex:
        #         log.warning("Error reading XMP: %r", ex)
        # def extract_metadata(self, pdf, entity):
        #     meta = pdf.metadata
        #     if meta is not None:
        #         entity.add("title", meta.get("title"))
        #         entity.add("author", meta.get("author"))
        #         entity.add("generator", meta.get("creator"))
        #         entity.add("generator", meta.get("producer"))
        #         entity.add("keywords", meta.get("subject"))

        for info in doc.info:
            pprint(info)

        if "Metadata" in doc.catalog:
            metadata = resolve1(doc.catalog["Metadata"]).get_data()
            pprint(XMPParser(metadata).meta)

    def pdf_extract(self, entity, pdf_path, extract_metadata=True):
        entity.schema = model.get("Pages")
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        fh = open(pdf_path, "rb")
        try:
            parser = PDFParser(fh)
            doc = PDFDocument(parser, "")
            doc.is_extractable = True
            if extract_metadata:
                self.pdf_metadata(entity, doc)
            for page_no, page in enumerate(PDFPage.create_pages(doc), 1):
                self.extract_page(entity, interpreter, page, device, page_no)
        except (PSException, PDFException) as exc:
            raise ProcessingException("Error reading PDF: %s" % exc) from exc
        finally:
            device.close()
            fh.close()

    def pdf_alternative_extract(self, entity, pdf_path):
        checksum = self.manager.store(pdf_path)
        entity.set("pdfHash", checksum)
        self.pdf_extract(entity, pdf_path, extract_metadata=False)
