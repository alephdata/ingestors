aleph.directive('entityCountries', ['Metadata', function(Metadata) {
  var countries = {};

  Metadata.get().then(function(metadata) {
    countries = metadata.countries;
  });

  return {
    restrict: 'E',
    transclude: true,
    scope: {
      'entity': '='
    },
    templateUrl: 'templates/entities/countries.html',
    link: function (scope, element, attrs, model) {
      scope.countryNames = countries;
    }
  };
}]);
