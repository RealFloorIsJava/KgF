<?php
  /**
   * Represents a collection of hand cards
   */
  class Hand {
    /**
     * The number of cards per type on the hand (excluding STATEMENT)
     */
    const HAND_CARD_PER_TYPE = 6;
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
    public static function loadHand($participant) {
      return new Hand(HandCard::loadHandCards($participant), $participant);
    }

    /**
     * Private constructor to prevent instance creation
     */
    private function __construct($cards, $participant) {
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
     * Replenishes the hand
     */
    public function replenish() {
      $counts = array(
        "OBJECT" => self::HAND_CARD_PER_TYPE,
        "VERB" => self::HAND_CARD_PER_TYPE
      );
      foreach ($this->mHandCards as $handCard) {
        $counts[$handCard->getCard()->getType()]--;
      }
      foreach ($counts as $type => $needed) {
        HandCard::replenishHandFor($this->mParticipant, $type, $needed);
      }
      $this->mHandCards = HandCard::loadHandCards($this->mParticipant);
    }

    /**
     * Toggles a hand card from picked to not picked and vice versa
     */
    public function togglePicked($handId) {
      if (!isset($this->mHandCards[$handId])) {
        // This hand card does not exist in this hand...
        return;
      }

      $hc = $this->mHandCards[$handId];
      if ($hc->isPicked()) {
        $pick = $hc->getPickId();
        foreach ($this->mHandCards as $handCard) {
          if ($handCard->isPicked() && $handCard->getPickId() >= $pick) {
            $handCard->unpick();
          }
        }
      } else {
        $maxPicked = $this->mParticipant->getMatch()->getCardGapCount();
        $nPicked = 0;
        $nextPickId = 0;
        foreach ($this->mHandCards as $handCard) {
          if ($handCard->isPicked()) {
            $nPicked++;
            $nextPickId = max($nextPickId, $handCard->getPickId() + 1);
          }
        }
        if ($nPicked >= $maxPicked) {
          // Can't pick new cards, too many on hand
          return;
        }
        $hc->pick($nextPickId);
      }
    }
  }
?>
