<!DOCTYPE html>
<html>
  <head>
    <title>Karten gegen Flopsigkeit</title>
    <link rel="shortcut icon" href="/favicon.ico">
    <link rel="stylesheet" type="text/css" href="/css/min/main.css">
    <?= $this->mUser->getThemeLoader() ?>
  </head>
  <body>
    <div class="cupboard">
      <a href="?logout">Log Out</a> &mdash;
      <a href="/global.php?page=match&amp;action=abandon">Abandon match</a>
      <div class="rightFloat">
        <a href="#" id="lightLabel">
          Lights are being checked...
        </a>
      </div>
      <div class="clearAfterFloat"></div>
    </div>
    <div class="match-container">
      <div class="match-view">
        <?= $this->getStatusFormat() ?>
        <div class="match-status" id="matchstatus">
          Loading...
        </div>
        <div class="part-container" id="partlist">
          <div class="part">
            <div class="part-name">Loading...</div>
          </div>
        </div>
        <div class="card-area">
          <div class="card-area-statement">
            <div class="side-slider">
              <div class="countdown-clock" id="countdown">
                00:00
              </div>
              <div class="card-base system-card sticky-card" id="match-statement">Waiting...</div>
            </div>
          </div>
          <div class="area-played-hand">
            <div class="card-area-played">
              <div class="card-area-boost">&nbsp;</div>
              <div class="card-area-boost">&nbsp;</div>
              <div class="card-area-boost">&nbsp;</div>
              <div class="card-area-boost">&nbsp;</div>
            </div>
            <div class="hand-area">
              <div class="hand-border">
                <div class="hand-tabs">
                  <div class="hand-tab-header" id="tab-actions">
                    Actions
                  </div>
                  <div class="hand-tab-header" id="tab-objects">
                    Objects
                  </div>
                </div>
                <div class="hand-area-set">
                  <div class="hand-area-set-row tab-actions" id="verb-hand">
                    <div class="card-base system-card">No cards on your hand.</div>
                  </div>
                  <div class="hand-area-set-row tab-objects" id="object-hand">
                    <div class="card-base system-card">No cards on your hand.</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="match-chat">
      <input type="text" class="chat-line" id="chatinput" spellcheck="false" maxlength="120" autocomplete="off">
      <div class="chat-messages" id="chatlist"></div>
      </div>
    </div>

    <script src="https://code.jquery.com/jquery-3.2.1.min.js" integrity="sha256-hwg4gsxgFZhOsEEamdOYGBf13FyQuiTwlAQgxVSNgt4=" crossorigin="anonymous"></script>
    <script type="text/javascript" src="/js/min/toolbox.js"></script>
    <script type="text/javascript" src="/js/min/matchview.js"></script>
    <script type="text/javascript" src="/js/min/theme.js"></script>
  </body>
</html>
