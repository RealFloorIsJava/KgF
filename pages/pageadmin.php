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

    /**
     * Constructor
     */
    public function __construct($user) {
      parent::__construct($user);
      if (!$this->user->is_admin()) {
        $this->fail_permission_check();
      }

      $this->subpage = isset($_GET["sub"]) ? $_GET["sub"] : "index";
      $this->action = isset($_GET["action"]) ? $_GET["action"] : "invalid";
    }

    /**
     * Dispatches actions to handler methods and sub page requests to the
     * specific templates
     */
    public function display() {
      $this->process_action();

      if ($this->subpage === "list") {
        $this->show_template("templates/admin-list.php");
      } else {
        $this->show_template("templates/admin.php");
      }
    }

    /**
     * Dispatcher for the more specific methods handling card actions
     */
    private function process_action() {
      if ($this->action === "delete") {
        $this->action_delete();
      } else if ($this->action === "mode-s") {
        $this->action_mode("STATEMENT");
      } else if ($this->action === "mode-o") {
        $this->action_mode("OBJECT");
      } else if ($this->action === "mode-v") {
        $this->action_mode("VERB");
      }
    }

    /**
     * Deletes the selected card
     */
    private function action_delete() {
      if (isset($_GET["card"])) {
        $card = Card::get_card($_GET["card"]);
        if ($card !== null) {
          $card->delete_card();
          $this->report_status("Card #".$_GET["card"]." deleted!", true);
        } else {
          $this->report_status(
            "Card #".$_GET["card"]." does not exist!", false);
        }
      }
    }

    /**
     * Changes the mode of the selected card
     */
    private function action_mode($mode) {
      if (isset($_GET["card"])) {
        $card = Card::get_card($_GET["card"]);
        if ($card !== null) {
          $card->set_mode($mode);
          $this->report_status(
            "Card #".$_GET["card"]."'s mode was changed!", true);
        } else {
          $this->report_status(
            "Card #".$_GET["card"]." does not exist!", false);
        }
      }
    }
  }
?>
