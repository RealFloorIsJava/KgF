<!DOCTYPE html>
<html>
  <head>
    <title>Karten gegen Flops</title>
    <style type="text/css">
      .floating-center {
        position: absolute;
        left: 37.5%;
        top: 37.5%;
        width: 25%;
        height: 25%;
        border: 1px solid gray;
        background-color: #f3f3f3;
      }
      .login-form {
        position: relative;
        top: 25px;
        left: 25px;
      }
      body {
        background-color: #eef3ee;
      }
    </style>
  </head>
  <body>
    <a href="https://github.com/LordKorea/KgF"><img style="position: absolute; top: 0; right: 0; border: 0;" src="https://camo.githubusercontent.com/e7bbb0521b397edbd5fe43e7f760759336b5e05f/68747470733a2f2f73332e616d617a6f6e6177732e636f6d2f6769746875622f726962626f6e732f666f726b6d655f72696768745f677265656e5f3030373230302e706e67" alt="Fork me on GitHub" data-canonical-src="https://s3.amazonaws.com/github/ribbons/forkme_right_green_007200.png"></a>
    <div class="floating-center">
      <div class="login-form">
        <form action="gate.php" method="POST">
          <label for="pw">Secret password:</label> <input type="password" id="pw" name="pw" size="20"><br>
          <input type="submit" value="Sign In">
        </form>
        <?php
          if (isset($_GET["pw_fail"])) {
            echo '<span style="color: #bb0000;">Incorrect password.</span>';
          } else if (isset($_GET["auth_fail"])) {
            echo '<span style="color: #bb0000;">Login required.</span>';
          }
        ?>
      </div>
    </div>
  </body>
</html>
