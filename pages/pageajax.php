<?php
    /**
     * The ajax handler
     */
    class PageAjax extends Page {
        /**
         * The action that was required
         */
        private $action;
        
        public function __construct($dbh, $user) {
            parent::__construct($dbh, $user);
            $this->action = isset($_GET["action"]) ? $_GET["action"] : "invalid";
        }
        
        public function display() {
            $this->process_action();
            
            // No display for now. Might be needed in the future
            // for two way communication
            echo "0";
        }
        
        private function process_action() {
            if ($this->action == "settheme") {
                $this->action_settheme();
            } else if ($this->action == "escalate") {
                $this->action_escalate();
            } else if ($this->action == "rename") {
                $this->action_rename();
            }
        }
        
        private function action_rename() {
            if (isset($_POST['name'])) {
                $name = htmlspecialchars($_POST['name']);
                if ($name != "" && strlen($name) < 64) {
                    $this->user->set_nickname($name);
                }
            }
        }
        
        private function action_escalate() {
            if (isset($_POST['token'])) {
                $token = sha1($_POST['token']);
                $correct_token = trim(file_get_contents("config/mgr_password"));
                if ($token == $correct_token) {
                    $this->user->escalate_privileges();
                }
            }
        }
        
        private function action_settheme() {
            if (isset($_POST["selection"])) {
                $new_theme = $_POST["selection"];
                if ($new_theme == "dark" || $new_theme == "light") {
                    $this->user->set_theme($new_theme);
                }
            }
        }
    }
?>
