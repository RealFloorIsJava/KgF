<?php
  /**
   * The dashboard
   */
  class PageDashboard extends Page {

    public function __construct($user) {
      parent::__construct($user);
      $this->action = isset($_GET["action"]) ? $_GET["action"] : "invalid";
    }

    /**
     * Displays the page
     */
    public function display() {
      $this->process_action();

      $this->show_template("templates/dashboard.php");
    }

    /**
     * Dispatcher for more specific actions
     */
    private function process_action() {
      if ($this->action === "matchlist") {
        $this->action_matchlist();
        exit();
      }
    }

    /**
     * Lists all matches.
     */
    private function action_matchlist() {
      $matches = Match::get_all_matches();
      $tojson = array();
      foreach ($matches as $match) {
        $tojson[] = array(
          "id" => $match->get_id(),
          "owner" => $match->get_owner_name(),
          "participants" => $match->get_participant_count(),
          "started" => $match->has_started(),
          "seconds" => $match->get_seconds_to_next_phase()
        );
      }
      echo json_encode($tojson);
    }
  }
?>
