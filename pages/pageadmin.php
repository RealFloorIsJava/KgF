<?php
  require_once "model/page.php";
  require_once "model/card.php";

  /**
   * The admin CP
   */
  class PageAdmin extends Page {
    /**
     * The sub page of the current page
     */
    private $mSubpage;
    /**
     * The action that was required
     */
    private $mAction;

    /**
     * Constructor
     */
    public function __construct($user) {
      parent::__construct($user);
      if (!$this->mUser->isAdmin()) {
        $this->failPermissionCheck();
      }

      $this->mSubpage = isset($_GET["sub"]) ? $_GET["sub"] : "index";
      $this->mAction = isset($_GET["action"]) ? $_GET["action"] : "invalid";
    }

    /**
     * Dispatches actions to handler methods and sub page requests to the
     * specific templates
     */
    public function display() {
      $this->processAction();

      if ($this->mSubpage === "list") {
        $this->showTemplate("templates/admin-list.php");
      } else {
        $this->showTemplate("templates/admin.php");
      }
    }

    /**
     * Dispatcher for the more specific methods handling card actions
     */
    private function processAction() {
      if ($this->mAction === "delete") {
        $this->actionDelete();
      } else if ($this->mAction === "mode-s") {
        $this->actionMode("STATEMENT");
      } else if ($this->mAction === "mode-o") {
        $this->actionMode("OBJECT");
      } else if ($this->mAction === "mode-v") {
        $this->actionMode("VERB");
      }
    }

    /**
     * Deletes the selected card
     */
    private function actionDelete() {
      if (isset($_GET["card"])) {
        $card = Card::getCard($_GET["card"]);
        if ($card !== null) {
          $card->deleteCard();
          $this->reportStatus("Card #".$_GET["card"]." deleted!", true);
        } else {
          $this->reportStatus(
            "Card #".$_GET["card"]." does not exist!", false);
        }
      }
    }

    /**
     * Changes the mode of the selected card
     */
    private function actionMode($mode) {
      if (isset($_GET["card"])) {
        $card = Card::getCard($_GET["card"]);
        if ($card !== null) {
          $card->setMode($mode);
          $this->reportStatus(
            "Card #".$_GET["card"]."'s mode was changed!", true);
        } else {
          $this->reportStatus(
            "Card #".$_GET["card"]." does not exist!", false);
        }
      }
    }
  }
?>
