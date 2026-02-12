from enum import Enum
from typing import Set, Optional
from app.models.nft import NFTStatus


class NFTStateMachine:
    """NFT lifecycle state machine."""

    VALID_TRANSITIONS: dict[NFTStatus, Set[NFTStatus]] = {
        NFTStatus.PENDING: {NFTStatus.MINTED, NFTStatus.BURNED},
        NFTStatus.MINTED: {NFTStatus.TRANSFERRED, NFTStatus.LOCKED, NFTStatus.BURNED},
        NFTStatus.TRANSFERRED: {NFTStatus.LOCKED, NFTStatus.BURNED, NFTStatus.TRANSFERRED},
        NFTStatus.LOCKED: {NFTStatus.MINTED, NFTStatus.BURNED},
        NFTStatus.BURNED: set(),
    }

    @staticmethod
    def can_transition(current_state: NFTStatus, target_state: NFTStatus) -> bool:
        return target_state in NFTStateMachine.VALID_TRANSITIONS.get(current_state, set())

    @staticmethod
    def get_valid_transitions(current_state: NFTStatus) -> Set[NFTStatus]:
        return NFTStateMachine.VALID_TRANSITIONS.get(current_state, set())

    @staticmethod
    def validate_transition(current_state: NFTStatus, target_state: NFTStatus) -> Optional[str]:
        if current_state == target_state:
            return "NFT is already in this state"
        if not NFTStateMachine.can_transition(current_state, target_state):
            valid_states = NFTStateMachine.get_valid_transitions(current_state)
            return f"Cannot transition from {current_state} to {target_state}. Valid states: {valid_states}"
        return None
