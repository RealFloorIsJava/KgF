<!DOCTYPE html>
<html>
  <head>
    <title>Admin CP</title>
    <link rel="stylesheet" type="text/css" href="/css/main.css">
    <?= $this->mUser->getThemeLoader() ?>
  </head>
  <body>
    <div class="cupboard">
      <a href="?logout">Log Out</a>
      <div style="float: right;">
        <a href="/global.php?page=admin&amp;sub=index">
          Admin CP tool selection
        </a> &mdash;
        <a href="/global.php?page=dashboard">Dashboard</a> &mdash;
        <a href="#" onclick="toggleLights()" id="lightLabel">
          Lights are being checked...
        </a>
      </div>
      <div style="clear: both;"></div>
    </div>
    <?= $this->getStatusFormat() ?>
    <div class="card-container">
      <?php
        $cards = Card::getAllCards();
        foreach ($cards as $card) {
      ?>
      <div class="card-base <?= $card->getTypeClass() ?>">
        <?= $card->getFormattedText() ?>
        <div class="card-id">
          <a href="/global.php?page=admin&amp;sub=list&amp;action=mode-s&amp;card=<?= $card->getId() ?>" class="knob-statement">&nbsp;&nbsp;&nbsp;&nbsp;</a> -
          <a href="/global.php?page=admin&amp;sub=list&amp;action=mode-o&amp;card=<?= $card->getId() ?>" class="knob-object">&nbsp;&nbsp;&nbsp;&nbsp;</a> -
          <a href="/global.php?page=admin&amp;sub=list&amp;action=mode-v&amp;card=<?= $card->getId() ?>" class="knob-verb">&nbsp;&nbsp;&nbsp;&nbsp;</a> -
          <a href="/global.php?page=admin&amp;sub=list&amp;action=delete&amp;card=<?= $card->getId() ?>">Delete</a> -
          #<?= $card->getId() ?>
        </div>
      </div>
      <?php
        }
      ?>
    </div>
    <script src="https://code.jquery.com/jquery-3.2.1.min.js" integrity="sha256-hwg4gsxgFZhOsEEamdOYGBf13FyQuiTwlAQgxVSNgt4=" crossorigin="anonymous"></script>
    <script type="text/javascript" src="/js/theme.js"></script>
  </body>
</html>
