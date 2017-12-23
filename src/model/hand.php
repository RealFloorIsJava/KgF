<?php
  /**
   * Represents a collection of hand cards
   */
  class Hand {
    /**
     * The cards in this hand
     */
    private $mHandCards;
    /**
     * The participant this hand belongs to
     */
    private $mParticipant;

    /**
     * Loads the hand of a participant
     */
    public static function loadHand(Participant $participant) {
      return new Hand(HandCard::loadHandCards($participant), $participant);
    }

    /**
     * Private constructor to prevent instance creation
     */
    private function __construct(array $cards, Participant $participant) {
      $this->mHandCards = $cards;
      $this->mParticipant = $participant;
    }

    /**
     * Hand card getter
     */
    public function getHandCards() {
      return $this->mHandCards;
    }

    /**
     * Reloads the hand
     */
    public function reload() {
      $this->mHandCards = HandCard::loadHandCards($this->mParticipant);
    }

    /**
     * Toggles a hand card from chosen to not chosen and vice versa
     */
    public function toggleChosen($handId) {
      $handId = intval($handId);
      if (!isset($this->mHandCards[$handId])) {
        // This hand card does not exist in this hand...
        return;
      }

      $hc = $this->mHandCards[$handId];
      if ($hc->isChosen()) {
        $choice = $hc->getChoiceId();
        foreach ($this->mHandCards as $handCard) {
          if ($handCard->isChosen() && $handCard->getChoiceId() >= $choice) {
            $handCard->unchoose();
          }
        }
      } else {
        $maxChoices = $this->mParticipant->getMatch()->getCardGapCount();
        $nChoices = 0;
        $nextChoiceId = 0;
        foreach ($this->mHandCards as $handCard) {
          if ($handCard->isChosen()) {
            $nChoices++;
            $nextChoiceId = max($nextChoiceId, $handCard->getChoiceId() + 1);
          }
        }
        if ($nChoices >= $maxChoices) {
          // Can't choose new cards, too many on hand
          return;
        }
        $hc->choose($nextChoiceId);
      }
    }

    /**
     * Returns the number of chosen cards on this hand
     */
    public function getChoiceCount() {
      $n = 0;
      foreach ($this->mHandCards as $handCard) {
        if ($handCard->isChosen()) {
          $n++;
        }
      }
      return $n;
    }

    /**
     * Unchooses all cards in this hand
     */
    public function unchooseAll() {
      foreach ($this->mHandCards as $handCard) {
        if ($handCard->isChosen()) {
          $handCard->unchoose();
        }
      }
    }

    /**
     * Deletes all chosen cards
     */
    public function deleteChosen() {
      $delIds = array();
      foreach ($this->mHandCards as $handId => $handCard) {
        if ($handCard->isChosen()) {
          $delIds[] = $handId;
          $handCard->delete();
        }
      }
      foreach ($delIds as $id) {
        unset($this->mHandCards[$id]);
      }
    }

    /**
     * Fetches the information about the chosen cards in this hand
     */
    public function getChooseData($redacted) {
      $redacted = boolval($redacted);
      $data = array();
      foreach ($this->mHandCards as $handId => $handCard) {
        if ($handCard->isChosen()) {
          if ($redacted) {
            $data[$handCard->getChoiceId()] = array(
              "redacted" => true
            );
          } else {
            $data[$handCard->getChoiceId()] = array(
              "type" => $handCard->getCard()->getType(),
              "text" => $handCard->getCard()->getText()
            );
          }
        }
      }
      ksort($data);
      return array_values($data);
    }
  }
?>
