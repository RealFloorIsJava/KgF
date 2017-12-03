function getFormatted(str) {
  return str.replace(/\|/g, "&shy;").replace(/_/g,
    "<u>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u>");
}
