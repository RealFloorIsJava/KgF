function getFormatted(str) {
  return str.replace(/\|/g, "&shy;").replace(/_/g,
    "<u>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u>");
}

function symmetricKeyDifference(a, b) {
  var onlyA = [];
  var onlyB = [];
  for (var x in a) {
    if (!b.hasOwnProperty(x)) {
      onlyA.push(x);
    }
  }
  for (var x in b) {
    if (!a.hasOwnProperty(x)) {
      onlyB.push(x);
    }
  }
  return {
    "onlyA": onlyA,
    "onlyB": onlyB
  };
}
