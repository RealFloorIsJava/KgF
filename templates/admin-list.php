<!DOCTYPE html>
<html>
  <head>
    <title>Admin CP</title>
    <link rel="stylesheet" type="text/css" href="/css/main.css">
    <?= $this->user->get_theme_loader() ?>
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
    <?= $this->get_status_format() ?>
    <div class="card-container">
      <?php
      $cards = Card::get_all_cards();
      foreach ($cards as $card) {
      ?>
      <div class="card-base <?= $card->get_type_class() ?>">
        <?= $card->get_formatted_text() ?>
        <div class="card-id">
          <a href="/global.php?page=admin&amp;sub=list&amp;action=mode-s&amp;card=<?= $card->get_id() ?>" class="knob-statement">&nbsp;&nbsp;&nbsp;&nbsp;</a> -
          <a href="/global.php?page=admin&amp;sub=list&amp;action=mode-o&amp;card=<?= $card->get_id() ?>" class="knob-object">&nbsp;&nbsp;&nbsp;&nbsp;</a> -
          <a href="/global.php?page=admin&amp;sub=list&amp;action=mode-v&amp;card=<?= $card->get_id() ?>" class="knob-verb">&nbsp;&nbsp;&nbsp;&nbsp;</a> -
          <a href="/global.php?page=admin&amp;sub=list&amp;action=delete&amp;card=<?= $card->get_id() ?>">Delete</a> -
          #<?= $card->get_id() ?>
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
