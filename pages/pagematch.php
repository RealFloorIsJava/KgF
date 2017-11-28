<?php
  /**
   * The match page
   */
  class PageMatch extends Page {
    /**
     * The action that was required
     */
    private $action;
    /**
     * The subpage that was requested
     */
    private $subpage;
    /**
     * The participant object that describes the user
     */
    protected $participant;
    /**
     * The match the user participates in
     */
    protected $match;

    /**
     * Constructor
     */
    public function __construct($user) {
      parent::__construct($user);
      $this->action = isset($_GET["action"]) ? $_GET["action"] : "invalid";
      $this->subpage = isset($_GET["sub"]) ? $_GET["sub"] : "invalid";
    }

    /**
     * Display the match page
     */
    public function display() {
      if ($this->action === "create") {
        $this->action_create();
      } else if ($this->action === "join") {
        $this->action_join();
      }

      // The user has to participate in a match from this point on
      $part = Participant::get_participant($this->user->get_id());
      if ($part === null) {
        $this->fail_permission_check();
      }
      $this->participant = $part;
      $this->match = $part->get_match();

      // Register a heartbeat for this user
      $this->participant->heartbeat(15);

      $this->process_action();

      if ($this->subpage === "view") {
        $this->show_template("templates/match.php");
      }
    }

    /**
     * Join a match
     */
    private function action_join() {
      $part = Participant::get_participant($this->user->get_id());
      if ($part === null) {
        if (isset($_GET["match"])) {
          $id = $_GET["match"];
          $match = Match::get_by_id($id);
          $match->add_user($this->user, time() + 15);
        }
      }

      // If the user is already in a match just redirect them to the match
      // view anyways to reopen their match.
      header("Location: /global.php?page=match&sub=view");
      exit();
    }

    /**
     * Creates a new match
     */
    private function action_create() {
      $part = Participant::get_participant($this->user->get_id());
      if ($part !== null) {
        // The user is participant in a match. Creating is not allowed.
        $this->fail_permission_check();
      }

      $statement = Card::random_card("STATEMENT");
      $match = Match::create_empty(time() + 60, $statement);
      $match->add_user($this->user, time() + 15);

      header("Location: /global.php?page=match&sub=view");
      exit();
    }

    /**
     * Sends a chat message from the current user to the current match
     */
    private function action_chatsend() {
      // The unprocessed message may be at most 150 characters long
      // With processed characters (html escapes) the message may not
      // exceed 200 characters. Empty messages are not allowed, spaces in the
      // beginning and end are ignored.
      if (isset($_POST["message"]) && strlen($_POST["message"]) < 150) {
        $text = trim(htmlspecialchars($_POST["message"]));
        if (strlen($text) > 0 && strlen($text) < 200) {
          if ($this->user->may_chat()) {
            ChatMessage::send_message($this->match, "USER",
              "<b>".$this->participant->get_name()."</b>: ".$text);
            $this->user->prevent_chat_until(time() + 1);
          }
        }
      }
    }

    /**
     * Abandons the current match
     */
    private function action_abandon() {
      $this->participant->leave_match();
      header("Location: /global.php?page=dashboard");
      exit();
    }

    private function action_participants() {
      $parts = $this->match->get_participants();
      $tojson = array();
      foreach ($parts as $part) {
        $tojson[] = array(
          "id" => $part->get_id(),
          "name" => $part->get_name(),
          "score" => $part->get_score()
        );
      }
      echo json_encode($tojson);
    }

    /**
     * Loads the chat messages starting at an offset
     */
    private function action_chat() {
      if (!isset($_POST["offset"])) {
        // Load all messages
        $offset = 0;
      } else {
        // Load all messages beginning from the given offset (in terms of
        // message ID)
        $offset = abs(intval($_POST["offset"]));
      }
      $msgs = ChatMessage::load_for_match($this->match, $offset);
      $tojson = array();
      foreach ($msgs as $msg) {
        $tojson[] = array(
        "id" => $msg->get_id(),
        "type" => $msg->get_type(),
        "message" => $msg->get_message()
        );
      }
      echo json_encode($tojson);
    }

    /**
     * Fetches the match status
     */
    private function action_status() {
      echo json_encode(array(
        "timer" => $this->match->get_seconds_to_next_phase(),
        "status" => $this->match->get_status()
      ));
    }

    /**
     * Dispatches actions to the specific handler methods
     */
    private function process_action() {
      if ($this->action === "abandon") {
        $this->action_abandon();
      } else if ($this->action === "participants") {
        $this->action_participants();
      } else if ($this->action === "chat") {
        $this->action_chat();
      } else if ($this->action === "chatsend") {
        $this->action_chatsend();
      } else if ($this->action === "status") {
        $this->action_status();
      }
    }
  }
?>
