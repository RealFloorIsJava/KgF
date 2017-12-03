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

      $this->processAction();

      $this->showTemplate("templates/dashboard.php");
    }

    /**
     * Dispatcher for more specific actions
     */
    private function processAction() {
      if ($this->mAction === "matchlist") {
        $this->actionMatchList();
        exit();
      }
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
