"use strict";

/**
 * Filters an iterator.
 *
 * @param cnd The condition used for filtering.
 */
function* itFilter(cnd) {
  for (let elem of this) {
    if (cnd(elem)) {
      yield elem
    }
  }
}

/**
 * Maps an iterator.
 *
 * @param fun The function to apply to the elements.
 */
function* itMap(fun) {
  for (let elem of this) {
    yield fun(elem)
  }
}

/**
 * Unpacks the result of a jQuery selection.
 *
 * @param sel The selection.
 * @return An array of all children elements.
 */
function jqUnpack(sel) {
  let r = [];
  for (let k = 0; k < sel.length; k++) {
    r.push(sel.eq(k))
  }
  return r
}

// Add filter/map to builtin types
(function(){
  Map.prototype.__itUOldKeys = Map.prototype.keys
  Map.prototype.keys = function() {
    let x = this.__itUOldKeys()
    x.filter = itFilter
    x.map = itMap
    return x
  }

  Set.prototype.__itUOldValues = Set.prototype.values
  Set.prototype.values = function() {
    let x = this.__itUOldValues()
    x.filter = itFilter
    x.map = itMap
    return x
  }
  Set.prototype.keys = Set.prototype.values

  let genFun = Object.getPrototypeOf(function*(){}).constructor
  genFun.prototype.filter = itFilter
  genFun.prototype.map = itMap
})()
