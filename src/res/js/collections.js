/**
 * Part of KgF.
 *
 * MIT License
 * Copyright (c) 2017 LordKorea
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to
 * deal in the Software without restriction, including without limitation the
 * rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
 * sell copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
 */
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
