<?php
  /**
   * The match page
   */
  class PageMatch extends Page {
    /**
     * The action that was required
     */
    private $mAction;
    /**
     * The subpage that was requested
     */
    private $mSubpage;
    /**
     * The participant object that describes the user
     */
    protected $mParticipant;
    /**
     * The match the user participates in
     */
    protected $mMatch;

    /**
     * Constructor
     */
    public function __construct($user) {
      parent::__construct($user);
      $this->mAction = isset($_GET["action"]) ? $_GET["action"] : "invalid";
      $this->mSubpage = isset($_GET["sub"]) ? $_GET["sub"] : "invalid";
    }

    /**
     * Display the match page
     */
    public function display() {
      if ($this->mAction === "create") {
        $this->actionCreate();
      } else if ($this->mAction === "join") {
        $this->actionJoin();
      }

      // The user has to participate in a match from this point on
      $part = Participant::getParticipant($this->mUser->getId());
      if ($part === null) {
        $this->failPermissionCheck();
      }
      $this->mParticipant = $part;
      $this->mMatch = $part->getMatch();

      // Check & update the gamestate
      $this->mMatch->refreshTimerIfNecessary();
      $this->mMatch->updateState();

      // If the match is not valid anymore, abort
      if ($this->mMatch->isDeleted()) {
        $this->failPermissionCheck();
      }

      // Register a heartbeat for this user
      $this->mParticipant->heartbeat(15);

      $this->processAction();

      if ($this->mSubpage === "view") {
        $this->showTemplate("templates/match.php");
      }
    }

    /**
     * Join a match
     */
    private function actionJoin() {
      $part = Participant::getParticipant($this->mUser->getId());
      if ($part === null) {
        if (isset($_GET["match"])) {
          $id = $_GET["match"];
          $match = Match::getById($id);
          if ($match === null || $match->hasStarted()) {
            $this->failPermissionCheck();
          }
          $match->addUser($this->mUser, time() + 15);
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
    private function actionCreate() {
      $part = Participant::getParticipant($this->mUser->getId());
      if ($part !== null) {
        // The user is participant in a match. Creating is not allowed.
        $this->failPermissionCheck();
      }

      // Check if the user provided a deck
      if (!isset($_FILES['deckupload'])) {
        $this->failPermissionCheck();
      }

      $file = $_FILES['deckupload'];
      if ($file["size"] >= 200000) {
        header("Location: /global.php?page=dashboard&deckfail=1");
        exit();
      }
      $fileName = "./uploads/f".md5(uniqid("f", true));
      if (!move_uploaded_file($file["tmp_name"], $fileName)) {
        $this->failPermissionCheck();
      }
      chmod($fileName, 0644);

      $match = Match::createEmpty();
      $match->addUser($this->mUser, time() + 15);
      $match->createMatchDeck($fileName);
      unlink($fileName);

      header("Location: /global.php?page=match&sub=view");
      exit();
    }

    /**
     * Sends a chat message from the current user to the current match
     */
    private function actionChatSend() {
      // The unprocessed message may be at most 150 characters long
      // With processed characters (html escapes) the message may not
      // exceed 200 characters. Empty messages are not allowed, spaces in the
      // beginning and end are ignored.
      if (isset($_POST["message"]) && strlen($_POST["message"]) < 150) {
        $text = trim(htmlspecialchars($_POST["message"]));
        if (strlen($text) > 0 && strlen($text) < 200) {
          if ($this->mUser->mayChat()) {
            $this->mMatch->getChat()->sendMessage("USER",
              "<b>".$this->mParticipant->getName()."</b>: ".$text);
            $this->mUser->preventChatUntil(time() + 1);
          }
        }
      }
    }

    /**
     * Abandons the current match
     */
    private function actionAbandon() {
      $this->mParticipant->leaveMatch();
      header("Location: /global.php?page=dashboard");
      exit();
    }

    private function actionParticipants() {
      $parts = $this->mMatch->getParticipants();
      $toJson = array();
      foreach ($parts as $part) {
        $toJson[] = array(
          "id" => $part->getId(),
          "name" => $part->getName(),
          "score" => $part->getScore(),
          "picking" => $part->isPicking()
        );
      }
      echo json_encode($toJson);
    }

    /**
     * Loads the chat messages starting at an offset
     */
    private function actionChat() {
      if (!isset($_POST["offset"])) {
        // Load all messages
        $offset = 0;
      } else {
        // Load all messages beginning from the given offset (in terms of
        // message ID)
        $offset = abs(intval($_POST["offset"]));
      }
      $msgs = $this->mMatch->getChat()->load($offset);
      $toJson = array();
      foreach ($msgs as $msg) {
        $toJson[] = array(
        "id" => $msg->getId(),
        "type" => $msg->getType(),
        "message" => $msg->getMessage()
        );
      }
      echo json_encode($toJson);
    }

    /**
     * Fetches the match status
     */
    private function actionStatus() {
      $data = array(
        "timer" => $this->mMatch->getSecondsToNextPhase(),
        "status" => $this->mMatch->getStatus(),
        "ending" => $this->mMatch->isEnding(),
        "hasCard" => $this->mMatch->hasCard(),
        "hand" => array(
          "OBJECT" => array(),
          "VERB" => array()
        ),
        "gaps" => $this->mMatch->getCardGapCount()
      );
      if ($this->mMatch->hasCard()) {
        $data["cardText"] = $this->mMatch->getCard()->getText();
      }
      foreach ($this->mParticipant->getHand() as $handId => $card) {
        $data["hand"][$card->getType()][$handId] = $card->getText();
      }
      echo json_encode($data);
    }

    /**
     * Dispatches actions to the specific handler methods
     */
    private function processAction() {
      if ($this->mAction === "abandon") {
        $this->actionAbandon();
      } else if ($this->mAction === "participants") {
        $this->actionParticipants();
      } else if ($this->mAction === "chat") {
        $this->actionChat();
      } else if ($this->mAction === "chatsend") {
        $this->actionChatSend();
      } else if ($this->mAction === "status") {
        $this->actionStatus();
      }
    }
  }
?>
