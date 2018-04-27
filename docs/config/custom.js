/*!
 * Copyright 2016 - 2018  Ternaris.
 * SPDX-License-Identifier: CC0-1.0
 */

window.marv_extensions = {
  formats: {
    // replace default datetime formatter, show times in UTC
    'datetime': function(date) { return new Date(date).toUTCString(); }
  },
  widgets: {
    // rowcount widget displays the number of rows in a table
    'rowcount': [
      /* insert callback, renders the data

        @function insert
        @param {HTMLElement} element The parent element
        @param {Object} data The data to be rendered
        @return {Object} state Any variable, if required by remove
      */
      function insert(element, data) {
        const doc = element.ownerDocument;
        const el = doc.createTextNode(data.rows.length + ' rows');
        element.appendChild(el);

        const state = { el };
        return state;
      },

      /* remove callback, clean up if necessary

        @function remove
        @param {Object} state The state object returned by insert
      */
      function remove(state) {
        state.el.remove();
      }
    ]
  }
};
