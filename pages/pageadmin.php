<?php
    /**
     * The admin CP
     */
    class PageAdmin extends Page {
        /**
         * The sub page of the current page
         */
        private $subpage;
        /**
         * The action that was required
         */
        private $action;
        
        public function __construct($user) {
            parent::__construct($user);
            if (!$this->user->is_admin()) {
                $this->fail_permission_check();
            }
            $this->subpage = isset($_GET["sub"]) ? $_GET["sub"] : "index";
            $this->action = isset($_GET["action"]) ? $_GET["action"] : "invalid";
        }
        
        public function display() {
            $this->process_action();
            
            if ($this->subpage == "list") {
                $this->show_template("templates/admin-list.php");
            } else {
                $this->show_template("templates/admin.php");
            }
        }
        
        private function process_action() {
            if ($this->action == "delete") {
                $this->action_delete();
            } else if ($this->action == "mode-s") {
                $this->action_mode("STATEMENT");
            } else if ($this->action == "mode-o") {
                $this->action_mode("OBJECT");
            } else if ($this->action == "mode-v") {
                $this->action_mode("VERB");
            }
        }
        
        private function action_delete() {
            if (isset($_GET["card"])) {
                $card = Card::get_card($_GET["card"]);
                if ($card !== null) {
                    $card->delete_card();
                    $this->report_status("Card #".$_GET["card"]." deleted!", true);
                } else {
                    $this->report_status("Card #".$_GET["card"]." does not exist!", false);
                }
            }
        }
        
        private function action_mode($mode) {
            if (isset($_GET["card"])) {
                $card = Card::get_card($_GET["card"]);
                if ($card !== null) {
                    $card->set_mode($mode);
                    $this->report_status("Card #".$_GET["card"]."'s mode was changed!", true);
                } else {
                    $this->report_status("Card #".$_GET["card"]." does not exist!", false);
                }
            }
        }
    }
?>
