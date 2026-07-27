/**
 * @file
 * Contains definition of the behaviour AOS.js.
 */

(function ($, Drupal, drupalSettings, once) {
  "use strict";

  Drupal.behaviors.aosInit = {
    attach: function (context, settings) {
      // Make it AOS.init() comment if you want to
      // call in your Theme/Module Javascript file.
      AOS.init();

      // You can also pass an optional settings object default settings.
    }
  };

})(jQuery, Drupal, drupalSettings, once);
