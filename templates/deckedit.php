<!DOCTYPE html>
<html>
  <head>
    <title>Karten gegen Flopsigkeit</title>
    <link rel="shortcut icon" href="/favicon.ico">
    <link rel="stylesheet" type="text/css" href="/css/main.css">
    <?= $this->mUser->getThemeLoader() ?>
  </head>
  <body>
    <div class="cupboard">
      <a href="?logout">Log Out</a> -
      <a href="/global.php?page=dashboard">Close editor</a>
      <div style="float: right;">
        <a href="#" onclick="toggleLights()" id="lightLabel">
          Lights are being checked...
        </a>
      </div>
      <div style="clear: both;"></div>
    </div>
    <?= $this->getStatusFormat() ?>

    <div class="match-box">
      <input type="file" id="deckinput" accept=".tsv">
      <div style="float: right;">
        <button style="font-size: large;" onclick="deckjs.openDeck()">
          Open deck
        </button>
        <button style="font-size: large;" onclick="deckjs.addCard()">
          Add card
        </button>
        <button style="font-size: large;" onclick="deckjs.sortCards()">
          Sort by type
        </button>
        <button style="font-size: large;" onclick="deckjs.exportDeck()">
          Export deck
        </button>
      </div>
      <div style="clear: both;"></div>
    </div>

    <div class="card-container" id="deck-display">
    </div>

    <div class="card-editor-container">
      <div class="card-editor-cover">&nbsp;</div>
      <div class="card-editor">
        <div class="card-editor-card-display"></div>
        <b>Underscore (_):</b> Represents a gap for statement cards (at most 3 per card)<br>
        <b>Pipe (|):</b> Represents a hyphenation point for long words<br>
        <input type="text" size="70" maxlength="250" id="card-text-input" class="card-text-edit"><br>
        <button style="font-size: large;" onclick="deckjs.closeEditor()">
          Save card
        </button>
      </div>
    </div>

    <script src="https://code.jquery.com/jquery-3.2.1.min.js" integrity="sha256-hwg4gsxgFZhOsEEamdOYGBf13FyQuiTwlAQgxVSNgt4=" crossorigin="anonymous"></script>
    <script type="text/javascript" src="/js/download.js"></script>
    <script type="text/javascript" src="/js/card.js"></script>
    <script type="text/javascript" src="/js/deck.js"></script>
    <script type="text/javascript" src="/js/theme.js"></script>
  </body>
</html>
