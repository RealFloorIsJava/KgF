<?php
  /**
   * Represents a distinct page of the application
   */
  class Page {
    /**
     * The user that initiated the request
     */
    protected $mUser;
    /**
     * The status message for the last action, if any.
     */
    private $mStatus;
    /**
     * Whether the last action was a success.
     */
    private $mSuccess;

    /**
     * Locates the file that needs to be included to open the given
     * page. If the page does not exist the include for a default
     * page will be used.
     * Returns an array (include, classname)
     */
    public static function getPageSource($pageName) {
      $page = "dashboard";
      if (preg_match("/[a-z]+/", $pageName)) {
        $page = $pageName;
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
      $this->mUser = $user;
      $this->mStatus = "";
      $this->mSuccess = true;
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
    protected function showTemplate($tpl) {
      eval("?>".file_get_contents($tpl));
    }

    /**
     * Can be used by specific pages to fail permission checks with
     * redirecting to the dashboard
     */
    protected function failPermissionCheck() {
      header("Location: /global.php");
    }

    /**
     * Returns a colored status bar (if necessary)
     */
    protected function getStatusFormat() {
      if ($this->mStatus !== "") {
        if ($this->mSuccess) {
          return '<div class="status-box success-box">'.$this->mStatus.'</div>';
        } else {
          return '<div class="status-box failure-box">'.$this->mStatus.'</div>';
        }
      }
      return "";
    }

    /**
     * Stores a status for later display
     */
    protected function reportStatus($status, $success) {
      $this->mStatus = $status;
      $this->mSuccess = $success;
    }
  }
?>
