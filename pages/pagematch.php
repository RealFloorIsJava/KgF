<?php
    /**
     * The match page
     */
    class PageMatch extends Page {
        /**
         * The action that was required
         */
        private $action;
        /**
         * The subpage that was requested
         */
        private $subpage;
        
        public function __construct($dbh, $user) {
            parent::__construct($dbh, $user);
            $this->action = isset($_GET["action"]) ? $_GET["action"] : "invalid";
            $this->subpage = isset($_GET["sub"]) ? $_GET["sub"] : "invalid";
        }
        
        public function display() {
            if ($this->action == "create") {
                $this->action_create();
            }
            
            // If the user has not created a match, they have to be in a match from this point on
            if (!Participant::is_in_match($this->user->get_id())) {
                $this->fail_permission_check();
            }
            
            $this->process_action();
            
            if ($this->subpage == "view") {
                $this->show_template("templates/match.php");
            }
        }
        
        private function action_create() {
            if (Participant::is_in_match($this->user->get_id())) {
                $this->fail_permission_check();
            }
            
            $statement = Card::random_card("STATEMENT");
            $match = Match::create_empty(time() + 60, $statement);
            Participant::add_user_to_match($this->user, $match);
            
            header("Location: /global.php?page=match&sub=view");
            exit();
        }
        
        private function process_action() {
            if ($this->action == "abandon") {
                Participant::leave_matches($this->user->get_id());
                header("Location: /global.php?page=dashboard");
                exit();
            }
        }
    }
?>
