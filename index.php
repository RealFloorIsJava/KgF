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
