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
