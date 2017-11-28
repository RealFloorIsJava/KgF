<?php
  require_once "model/page.php";

  /**
   * This class handles AJAX requests that do not fit to a certain page but
   * rather might be used anywhere.
   */
  class PageAjax extends Page {
    /**
     * The action that was required
     */
    private $action;

    /**
     * Constructor
     */
    public function __construct($user) {
      parent::__construct($user);
      $this->action = isset($_GET["action"]) ? $_GET["action"] : "invalid";
    }

    /**
     * Displays this page. For the AJAX handler this is only dispatching
     * the request to handler methods.
     */
    public function display() {
      $this->process_action();
    }

    /**
     * Dispatcher for the more specific handler methods
     */
    private function process_action() {
      if ($this->action === "settheme") {
        $this->action_settheme();
      } else if ($this->action === "escalate") {
        $this->action_escalate();
      } else if ($this->action === "rename") {
        $this->action_rename();
      }
    }

    /**
     * Renames the current user
     */
    private function action_rename() {
      // A name may not be empty and has to be shorter than 32 characters
      if (isset($_POST['name'])) {
        $name = htmlspecialchars($_POST['name']);
        if ($name !== "" && strlen($name) < 32) {
          $this->user->set_nickname($name);
        }
      }
    }

    /**
     * Escalates user privileges to admin (manager) privileges when the correct
     * manager password is given.
     */
    private function action_escalate() {
      if (isset($_POST['token'])) {
        $token = sha1($_POST['token']);
        $correct_token = trim(file_get_contents("config/mgr_password"));
        if ($token === $correct_token) {
          $this->user->escalate_privileges();
        }
      }
    }

    /**
     * Sets the theme for the user
     */
    private function action_settheme() {
      if (isset($_POST["selection"])) {
        $new_theme = $_POST["selection"];
        if ($new_theme === "dark" || $new_theme === "light") {
          $this->user->set_theme($new_theme);
        }
      }
    }
  }
?>
