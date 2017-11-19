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
        /**
         * The participant object that describes the user
         */
        private $participant;
        /**
         * The match the user participates in
         */
        private $match;
        
        public function __construct($dbh, $user) {
            parent::__construct($dbh, $user);
            $this->action = isset($_GET["action"]) ? $_GET["action"] : "invalid";
            $this->subpage = isset($_GET["sub"]) ? $_GET["sub"] : "invalid";
        }
        
        public function display() {
            if ($this->action == "create") {
                $this->action_create();
            }
            
            // The user has to participate in a match from this point on
            $part = Participant::get_participant($this->user->get_id());
            if ($part === null) {
                $this->fail_permission_check();
            }
            $this->participant = $part;
            $this->match = $part->get_match();
            
            // Register a heartbeat for this user
            $this->participant->heartbeat(15);
            
            $this->process_action();
            
            if ($this->subpage == "view") {
                $this->show_template("templates/match.php");
            }
        }
        
        private function action_create() {
            $part = Participant::get_participant($this->user->get_id());
            if ($part !== null) {
                $this->fail_permission_check();
            }
            
            $statement = Card::random_card("STATEMENT");
            $match = Match::create_empty(time() + 60, $statement);
            $match->add_user($this->user, time() + 15);
            
            header("Location: /global.php?page=match&sub=view");
            exit();
        }
        
        private function action_abandon() {
            $this->participant->leave_match();
            header("Location: /global.php?page=dashboard");
            exit();
        }
        
        private function process_action() {
            if ($this->action == "abandon") {
                $this->action_abandon();
            }
        }
    }
?>
