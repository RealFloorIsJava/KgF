<!DOCTYPE html>
<html>
  <head>
    <title>Karten gegen Flopsigkeit</title>
    <link rel="stylesheet" type="text/css" href="/css/main.css">
    <?= $this->mUser->getThemeLoader() ?>
  </head>
  <body>
    <div class="cupboard">
      <a href="?logout">Log Out</a> &mdash;
      You are known as
      <span id="username"><?= $this->mUser->getNickname() ?></span>
      (<a href="#" onclick="changeName()">Change</a>)
      <div style="float: right;">
        <?php
          if ($this->mUser->isAdmin()) {
            echo '<a href="#" onclick="enterACP(true)">Admin CP</a>';
          } else {
            echo '<a href="#" onclick="enterACP(false)">Admin CP</a>';
          }
        ?> &mdash;
        <a href="#" onclick="toggleLights()" id="lightLabel">
          Lights are being checked...
        </a>
      </div>
      <div style="clear: both;"></div>
    </div>
    <?= $this->getStatusFormat() ?>

    <div id="matchlist">
      <div class="match-box">
        Please wait while matches are being loaded...
      </div>
    </div>

    <div class="match-box">
      <div style="float: right;">
        <button style="font-size: large;" onclick="createMatch()">
          Create new match
        </button>
      </div>
      <div style="clear: both;"></div>
    </div>

    <script src="https://code.jquery.com/jquery-3.2.1.min.js" integrity="sha256-hwg4gsxgFZhOsEEamdOYGBf13FyQuiTwlAQgxVSNgt4=" crossorigin="anonymous"></script>
    <script type="text/javascript" src="/js/dashboard.js"></script>
    <script type="text/javascript" src="/js/match.js"></script>
    <script type="text/javascript" src="/js/theme.js"></script>
  </body>
</html>
