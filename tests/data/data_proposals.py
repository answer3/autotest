from app.models.enums import PlanProposalStatus

REQUEST_PAYLOAD_TEST = {"schema_version": 1, "generator": "pytest"}

PROPOSAL_DATA_CREATE_1 = {
    "status": PlanProposalStatus.pending,
    "request_payload": REQUEST_PAYLOAD_TEST,
}

PROPOSAL_DATA_SUCCESS_1 = {
    "status": PlanProposalStatus.succeeded,
    "request_payload": REQUEST_PAYLOAD_TEST,
    "result_payload": {
        "steps": ["await page.goto('/login')"],
        "assertions": ["await expect(page).toHaveURL('/login')"]
    }
}

PROPOSAL_DATA_FAILED_1 = {
    "status": PlanProposalStatus.failed,
    "request_payload": REQUEST_PAYLOAD_TEST,
}

PROPOSAL_DATA_SUCCESS_READY_1 = {
    "status": PlanProposalStatus.succeeded,
    "request_payload": REQUEST_PAYLOAD_TEST,
    "result_payload": {
        "steps": ["await page.goto('/login')"],
        "assertions": ["await expect(page).toHaveURL('/login')"]
    },
    "is_ready_for_test": True
}
