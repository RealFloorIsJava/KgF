<?php
  /**
   * The dashboard
   */
  class PageDashboard extends Page {

    /**
     * Displays the page
     */
    public function display() {
      $this->show_template("templates/dashboard.php");
    }
  }
?>
