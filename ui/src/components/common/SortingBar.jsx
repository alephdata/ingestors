import React, { PureComponent } from 'react';
import { FormattedMessage, injectIntl } from 'react-intl';
import { Alignment, Button, Intent, MenuItem } from '@blueprintjs/core';
import SelectWrapper from 'src/components/common/SelectWrapper';

import './SortingBar.scss';

class SortingBar extends PureComponent {
  renderOption = (option, { handleClick }) => (
    <MenuItem
      key={option.field}
      onClick={handleClick}
      text={option.label}
    />
  )

  render() {
    const { activeDirection, activeSort, onSort, sortingOptions } = this.props;
    return (
      <div className="SortingBar">
        <div className="SortingBar__item">
          <span className="SortingBar__label">
            <FormattedMessage
              id="sorting.bar.label"
              defaultMessage="Sort by:"
            />
          </span>
          <div className="SortingBar__control">
            <SelectWrapper
              itemRenderer={this.renderOption}
              items={sortingOptions}
              onItemSelect={onSort}
              activeItem={activeSort}
              popoverProps={{
                minimal: true,
                fill: false,
                className: 'SortingBar__item__popover',
              }}
              inputProps={{
                fill: false,
              }}
              filterable={false}
              resetOnClose
              resetOnSelect
            >
              <Button
                text={activeSort.label}
                alignText={Alignment.LEFT}
                minimal
                intent={Intent.PRIMARY}
                rightIcon="caret-down"
              />
            </SelectWrapper>
          </div>
        </div>
        <div className="SortingBar__item">
          <span className="SortingBar__label">
            <FormattedMessage
              id="sorting.bar.direction"
              defaultMessage="Direction:"
            />
          </span>
          <div className="SortingBar__control">
            <Button
              icon={activeDirection === 'desc' ? 'arrow-down' : 'arrow-up'}
              onClick={() => onSort({ direction: activeDirection === 'desc' ? 'asc' : 'desc' })}
              minimal
              intent={Intent.PRIMARY}
            />
          </div>
        </div>
      </div>
    );
  }
}

export default injectIntl(SortingBar);
