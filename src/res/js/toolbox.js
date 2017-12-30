function getFormatted(str) {
  return str.replace(/\|/g, "&shy;").replace(/_/g,
    "<u>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u>");
}

function symmetricKeyDifference(a, b) {
  var onlyA = [];
  var onlyB = [];
  for (var x of a) {
    if (!b.has(x[0])) {
      onlyA.push(x[0]);
    }
  }
  for (var x of b) {
    if (!a.has(x[0])) {
      onlyB.push(x[0]);
    }
  }
  return {
    "onlyA": onlyA,
    "onlyB": onlyB
  };
}
