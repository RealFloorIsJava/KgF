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
      <a href="?logout">Log Out</a> &mdash;
      You are known as
      <span id="username"><?= $this->mUser->getNickname() ?></span>
      (<a href="#" id="nameChangeLabel">Change</a>)
      <div class="rightFloat">
        <a href="#" id="lightLabel">
          Lights are being checked...
        </a>
      </div>
      <div class="clearAfterFloat"></div>
    </div>
    <?= $this->getStatusFormat() ?>

    <div id="matchlist">
      <div class="match-box">
        Please wait while matches are being loaded...
      </div>
    </div>

    <div class="match-box">
      <form action="/global.php?page=match&amp;action=create" method="POST" enctype="multipart/form-data">
      <span class="upload-hint">Choose a deck...</span>
        <input type="file" name="deckupload" required="required" accept=".tsv">
        <span class="upload-hint">(Maximum file size for decks is <b>200kB</b>)</span>
        <div class="rightFloat">
          <input type="submit" value="Create new match" class="largeTextButton">
        </div>
      </form>
      <div class="clearAfterFloat"></div>
    </div>

    <div class="match-box">
      <div class="rightFloat">
        <button class="largeTextButton" id="deckEditButton">
          Open deck editor
        </button>
      </div>
      <div class="clearAfterFloat"></div>
    </div>

    <script src="https://code.jquery.com/jquery-3.2.1.min.js" integrity="sha256-hwg4gsxgFZhOsEEamdOYGBf13FyQuiTwlAQgxVSNgt4=" crossorigin="anonymous"></script>
    <script type="text/javascript" src="/js/dashboard.js"></script>
    <script type="text/javascript" src="/js/match.js"></script>
    <script type="text/javascript" src="/js/theme.js"></script>
  </body>
</html>
