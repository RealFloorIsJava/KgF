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
      <a href="/global.php?page=match&amp;action=abandon">Abandon match</a>
      <div style="float: right;">
        <a href="#" onclick="toggleLights()" id="lightLabel">
          Lights are being checked...
        </a>
      </div>
      <div style="clear: both;"></div>
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
              <div class="card-base statement-card sticky-card">
                This is a statement about
                <u>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u>.
                <div class="card-id">
                  #1234
                </div>
              </div>
            </div>
          </div>
          <div class="area-played-hand">
            <div class="card-area-played">
              <div class="card-area-set">
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
              </div>
              <div class="card-area-set">
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
              </div>
              <div class="card-area-set">
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
              </div>
              <div class="card-area-set">
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
              </div>
              <div class="card-area-set">
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
              </div>
              <div class="card-area-set">
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
              </div>
              <div class="card-area-set">
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
              </div>
              <div class="card-area-set">
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
              </div>
              <div class="card-area-set">
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
              </div>
              <div class="card-area-set">
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
              </div>
              <div class="card-area-set">
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
              </div>
              <div class="card-area-set">
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
                <div class="card-base object-card">Words<div class="card-id">#1234</div></div>
              </div>
            </div>
            <div class="hand-area">
              <div class="hand-border">
                <div class="hand-tabs">
                  <div class="hand-tab-header" id="tab-actions" onclick="pickTab('tab-actions')">
                    Actions
                  </div>
                  <div class="hand-tab-header" id="tab-objects" onclick="pickTab('tab-objects')">
                    Objects
                  </div>
                </div>
                <div class="hand-area-set">
                  <div class="hand-area-set-row tab-actions">
                    <div class="card-base verb-card" onclick="toggleSelect(this)">Chopping with a blunt axe<div class="card-id">#1234</div></div>
                    <div class="card-base verb-card" onclick="toggleSelect(this)">Chopping with a blunt axe<div class="card-id">#1234</div></div>
                    <div class="card-base verb-card" onclick="toggleSelect(this)">Chopping with a blunt axe<div class="card-id">#1234</div></div>
                    <div class="card-base verb-card" onclick="toggleSelect(this)">Chopping with a blunt axe<div class="card-id">#1234</div></div>
                    <div class="card-base verb-card" onclick="toggleSelect(this)">Chopping with a blunt axe<div class="card-id">#1234</div></div>
                    <div class="card-base verb-card" onclick="toggleSelect(this)">Chopping with a blunt axe<div class="card-id">#1234</div></div>
                  </div>
                  <div class="hand-area-set-row tab-objects">
                    <div class="card-base object-card" onclick="toggleSelect(this)">Words<div class="card-id">#1234</div></div>
                    <div class="card-base object-card" onclick="toggleSelect(this)">Words<div class="card-id">#1234</div></div>
                    <div class="card-base object-card" onclick="toggleSelect(this)">Words<div class="card-id">#1234</div></div>
                    <div class="card-base object-card" onclick="toggleSelect(this)">Words<div class="card-id">#1234</div></div>
                    <div class="card-base object-card" onclick="toggleSelect(this)">Words<div class="card-id">#1234</div></div>
                    <div class="card-base object-card" onclick="toggleSelect(this)">Words<div class="card-id">#1234</div></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="match-chat">
      <input type="text" class="chat-line" id="chatinput" spellcheck="false" maxlength="120">
      <div class="chat-messages" id="chatlist"></div>
      </div>
    </div>

    <script src="https://code.jquery.com/jquery-3.2.1.min.js" integrity="sha256-hwg4gsxgFZhOsEEamdOYGBf13FyQuiTwlAQgxVSNgt4=" crossorigin="anonymous"></script>
    <script type="text/javascript" src="/js/matchview.js"></script>
    <script type="text/javascript" src="/js/theme.js"></script>
  </body>
</html>
