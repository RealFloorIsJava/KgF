<?php
  /**
   * The dashboard
   */
  class PageDashboard extends Page {
    /**
     * The required action
     */
    private $mAction;

    /**
     * Constructor
     */
    public function __construct($user) {
      parent::__construct($user);
      $this->mAction = isset($_GET["action"]) ? $_GET["action"] : "invalid";
    }

    /**
     * Displays the page
     */
    public function display() {
      if (isset($_GET["deckfail"])) {
        $this->reportStatus("The uploaded file is too big!", false);
      }

      if ($this->processAction()) {
        return;
      }

      $this->showTemplate("templates/dashboard.php");
    }

    /**
     * Dispatcher for more specific actions
     */
    private function processAction() {
      // Prevent templates from being shown by returning true when an action
      // is processed
      if ($this->mAction === "matchlist") {
        $this->actionMatchList();
      } else {
        return false;
      }
      return true;
    }

    /**
     * Lists all matches.
     */
    private function actionMatchList() {
      $matches = Match::getAllMatches();
      $toJson = array();
      foreach ($matches as $match) {
        if ($match->isDeleted()) {
          continue;
        }
        $toJson[] = array(
          "id" => $match->getId(),
          "owner" => $match->getOwnerName(),
          "participants" => $match->getParticipantCount(),
          "started" => $match->hasStarted(),
          "seconds" => $match->getSecondsToNextPhase()
        );
      }
      echo json_encode($toJson);
    }
  }
?>
