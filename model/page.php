<?php
  /**
   * Represents a distinct page of the application
   */
  class Page {
    /**
     * The user that initiated the request
     */
    protected $user;
    /**
     * The status message for the last action, if any.
     */
    private $status;
    /**
     * Whether the last action was a success.
     */
    private $success;

    /**
     * Locates the file that needs to be included to open the given
     * page. If the page does not exist the include for a default
     * page will be used.
     * Returns an array (include, classname)
     */
    public static function get_page_source($page_name) {
      $page = "dashboard";
      if (preg_match("/[a-z]+/", $page_name)) {
        $page = $page_name;
      }
      $file = "pages/page".$page.".php";
      if (!file_exists($file)) {
        return array("pages/pagedashboard.php", "PageDashboard");
      }
      return array($file, "Page".ucfirst($page));
    }

    /**
     * Constructor
     */
    public function __construct($user) {
      $this->user = $user;
      $this->status = "";
      $this->success = true;
    }

    /**
     * Displays the page to the user (and performs necessary
     * calculations)
     */
    public function display() {
      die("Display not implemented!");
    }

    /**
     * Shows a template to the user
     */
    protected function show_template($tpl) {
      eval("?>".file_get_contents($tpl));
    }

    /**
     * Can be used by specific pages to fail permission checks with
     * redirecting to the dashboard
     */
    protected function fail_permission_check() {
      header("Location: /global.php");
      exit();
    }

    /**
     * Returns a colored status bar (if necessary)
     */
    protected function get_status_format() {
      if ($this->status !== "") {
        if ($this->success) {
          return '<div class="status-box success-box">'.$this->status.'</div>';
        } else {
          return '<div class="status-box failure-box">'.$this->status.'</div>';
        }
      }
      return "";
    }

    /**
     * Stores a status for later display
     */
    protected function report_status($status, $success) {
      $this->status = $status;
      $this->success = $success;
    }
  }
?>
