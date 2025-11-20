---
title: One-Shot Debugging Guarantee System (Procedural Guide)
description: A comprehensive procedural guide and methodology for advanced debugging, root cause analysis, and code hardening to be followed by the AI Executor (Cursor).
tags: debugging, methodology, root-cause-analysis, code-hardening, process-guide, advanced, ai-procedure
---
# One-Shot Debugging Guarantee System (Procedural Guide)
## I. Guide Metadata (Frontmatter)
*(This document outlines a comprehensive debugging methodology and set of best practices. While not a single checkable rule, it provides foundational procedures for the AI Executor.)*
```yaml
---
# ruleId: Unique identifier for this procedural guide.
ruleId: "debugging-framework-guide-001"
# description: What this guide covers.
description: "Comprehensive procedural guide for AI-driven debugging, root cause analysis, code protection, testing, and knowledge management related to bug fixing."
# severity: N/A for a guide, but sub-principles might imply severities for related actions.
severity: "INFO" # Indicates it's a guiding document.
# globs: N/A for a general procedural guide.
globs: ""
# alwaysApply: This guide's principles should always be considered by the AI when debugging.
alwaysApply: true
# tags: Keywords for categorization.
tags: ["debugging", "methodology", "root-cause-analysis", "code-hardening", "best-practices", "ai-procedure"]
# relatedRules: Links to specific granular rules that support or enforce aspects of this guide.
relatedRules: [ "issue-blocker-immediate-logging-001", "automated-test-requirements-001", "regression-testing-execution-001", "edge-case-test-creation-and-documentation-001", "enhanced-logging-practices-001", "api-client-error-handling-standard-001", "api-response-validation-001", "function-contract-assertion-generation-001", "bugfix-documentation-standard-001", "api-parameter-validation-at-entry-001", "consistent-error-typing-001", "filesystem-path-validation-001", "commit-standard-format-001", "component-validation-before-advancement-001", "threading-resource-cleanup-001", "ui-consistent-error-display-001", "startup-dependency-check-001", "patch-implementation-guidelines-001", # (New based on framework content) "code-annotation-best-practices-001", # (New based on framework content) "root-cause-causality-chain-documentation-001" # (New based on framework content) # Plus any other relevant existing granular rules from our full list
]
# autoFixable: N/A for a guide. AI *follows* the guide.
autoFixable: "NONE"
# version: Version of this guide.
version: "1.0"
# lastUpdated: Date last modified (AI to fill or user to update).
lastUpdated: "[YYYY-MM-DD]" # e.g., 2023-10-28
---
```

**content_copydownload**Use code [**with caution**](https://support.google.com/legal/answer/13505487).Markdown

## II. Procedural Guidelines & Methodologies

### A. Core Debugging Process

*(Guideline for the AI's fundamental approach when an error is encountered.)*

1. **Error Classification and Investigation Procedure:**
    - Categorize errors by subsystem (e.g., API, file system, threading, UI, dependencies).
    - Extract complete context from error messages, stack traces, and relevant logs (Ref: @enhanced-logging-practices-001.mdc).
    - Attempt to verify if the error is consistently reproducible before attempting fixes.
    - Trace error propagation through the call chain to identify the potential root cause.
2. **Five-Phase Debugging Methodology:**
    
    *(AI should follow this structured process for debugging significant issues.)*
    
    - **Phase 1: Observation**
        - Capture complete error information, including full stack traces.
        - Document the exact steps or conditions required to reproduce the error.
        - Identify and log relevant environment variables, system state, and input data at the time of the error (Ref: @issue-blocker-immediate-logging-001.mdc).
        - Log the state of relevant objects or variables proximate to the error location.
    - **Phase 2: Analysis**
        - Systematically follow the error propagation chain backward from the point of failure to its origin.
        - Consult internal knowledge base or previous bug logs for similar existing bugs or known problematic patterns.
        - Differentiate between the observed symptoms and the underlying root cause(s).
        - Map out affected components and consider potentially affected downstream components.
    - **Phase 3: Solution Design**
        - Formulate a clear plan for the fix, defining the scope of changes.
        - Identify and consider all potential side effects or regressions the fix might introduce.
        - Consider a layered solution if applicable (e.g., an immediate containment patch followed by a more robust long-term fix).
        - Prepare validation criteria and test cases (Ref: @automated-test-requirements-001.mdc, @edge-case-test-creation-and-documentation-001.mdc) *before* implementing the fix.
    - **Phase 4: Implementation**
        - Apply the minimal, targeted changes necessary to address the identified root cause (Ref: @patch-implementation-guidelines-001.mdc).
        - Strive to preserve existing interface contracts and minimize disruption to consumers of the modified code.
        - Update or add logging statements around the fix to aid future debugging and confirm fix behavior (Ref: @enhanced-logging-practices-001.mdc).
        - Document the rationale for the fix clearly in code comments (Ref: @code-annotation-best-practices-001.mdc) and commit messages (Ref: @commit-standard-format-001.mdc).
    - **Phase 5: Validation**
        - Verify that the implemented fix resolves the original reported issue (Ref: @component-validation-before-advancement-001.mdc).
        - Test edge cases specifically around the area of the fix (Ref: @edge-case-test-creation-and-documentation-001.mdc).
        - Conduct regression testing on related components and functionalities to ensure no new issues were introduced (Ref: @regression-testing-execution-001.mdc).
        - If feasible, monitor the system or component post-fix for any unintended consequences.

### B. Advanced Root Cause Analysis Techniques

*(For complex or elusive bugs, AI should employ these deeper analysis techniques.)*

1. **Comprehensive Root Cause Analysis (RCA) Procedure:**
    - **Falsifiable Hypotheses Testing:**
        - Formulate multiple distinct, competing hypotheses about the bug's cause.
        - Design and execute specific tests or checks that can definitively confirm or eliminate each incorrect hypothesis.
        - Require positive evidence for the root cause, not just correlation with symptoms.
        - Document ruled-out hypotheses to prevent redundant investigation in the future.
    - **Layered Causality Chain Mapping & Documentation:**
        - When performing RCA, document the identified causality chain from symptom to root cause (Ref: @root-cause-causality-chain-documentation-001.mdc).
        
        ```visual-basic
        # ✅ DO: Example of documenting the complete causality chain in a bug report or log
        # Bug: TypeError in process_playlist
        # Investigation Log - Causality Chain:
        # Layer 1 (Symptom): playlist_service.py:145 - TypeError when passing dict to process_playlist.
        # Layer 2 (Proximate Cause): PlaylistWorker instance in playlist_service.py received a dict for 'path' instead of a string.
        # Layer 3 (Contributing Factor): Unchecked parameter type for 'path' in PlaylistWorker.__init__ (playlist_service.py:45).
        # Layer 4 (Origin): playlist_input_view.py:212 - User options dictionary was passed directly to PlaylistWorker without extracting/converting the 'path' value.
        # ROOT CAUSE: Missing type conversion or data extraction in playlist_input_view.py:212 before instantiating PlaylistWorker.
        
        # ❌ DON'T: Stop analysis at the first error occurrence if it's just a symptom.
        ```
        
        
        
2. **Formal Change Impact Analysis Procedure:**
    - **Control Flow Impact Mapping:** Identify all code paths affected by the modified code. Map upstream/downstream dependencies.
    - **Data Flow Analysis & Documentation:** Trace the flow and mutation of key variables involved in data corruption or unexpected state issues.
        
        ```visual-basic
        # ✅ DO: Example of documenting variable mutations during analysis
        # Variable Trace: output_dir
        # - Initialized: playlist_input_view.py:205 (value: "/tmp/user_output", type: str)
        # - Passed to: playlist_service.PlaylistService.schedule_processing (arg: output_dir)
        # - Modified in: playlist_service.py:128 (prepended with date_prefix)
        
        # ❌ DON'T: Assume variables maintain type or value consistency without verification.
        ```
        
        
        

### C. Error Category-Specific Handling Guidelines

*(AI should apply these specific considerations based on the type of error encountered.)*

1. **File System Errors - Best Practices:**
    - Always validate path types. (Ref: @filesystem-path-validation-001.mdc).
    - Use try-except blocks around file operations, catching specific exceptions.
    - Handle platform-specific path conventions carefully (e.g., using os.path).
    - Test with invalid paths, long paths, special characters.
    - Verify necessary library dependencies (Ref: @startup-dependency-check-001.mdc).
    
    ```visual-basic
    # ✅ DO: Handle platform-specific paths with protection and type checking
    import os
    # from some_logger_module import logger # AI adapts logger usage
    
    def normalize_path_robustly(path_input):
        if not isinstance(path_input, (str, bytes, os.PathLike)):
            # logger.error(f"Invalid path type: {type(path_input)}")
            return os.path.abspath("default_output_location") 
        try:
            return os.path.abspath(str(path_input))
        except Exception as e:
            # logger.error(f"Error normalizing path '{path_input}': {e}")
            return os.path.abspath("default_output_location")
    
    # ❌ DON'T: Make unsafe assumptions about path format or type
    ```
    
    
    
2. **API Integration Errors - Best Practices:**
    - Implement robust error handling with retries. (Ref: @api-client-error-handling-standard-001.mdc).
    - Handle rate limiting gracefully.
    - Validate API responses. (Ref: @api-response-validation-001.mdc).
    - Test with mocked API failures.
    
    ```visual-basic
    # ✅ DO: Implement proper API error handling with retries
    # def get_playlist_data_robust(playlist_id, sp_client): # AI adapts
    # ... (full example from previous version) ...
    
    # ❌ DON'T: Catch all exceptions without specific handling
    ```
    
    
    
3. **Threading/Concurrency Issues - Best Practices:**
    - Ensure proper thread cleanup. (Ref: @threading-resource-cleanup-001.mdc).
    - Use robust inter-thread communication.
    - Implement timeout handling for long operations. (Ref: @long-operation-timeout-handling-001.mdc if defined).
    - Test with forced cancellation.
    
    ```visual-basic
    # ✅ DO: Properly manage thread lifecycle
    # class ThreadManager: # AI adapts
    # ... (full example from previous version) ...
    
    # ❌ DON'T: Leave threads hanging
    ```
    
    
    
4. **UI/Error Propagation - Best Practices:**
    - Implement consistent UI error handling. (Ref: @ui-consistent-error-display-001.mdc).
    - Display user-friendly error messages.
    - Use a robust error propagation system.
    - Test UI with simulated errors.
    
    ```visual-basic
    # ✅ DO: Handle UI errors with user-friendly messages
    # class MyQtWindow: # AI adapts
    # ... (full example from previous version) ...
    
    # ❌ DON'T: Allow unhandled exceptions in UI code
    ```
    
    
    
5. **Dependency Management - Best Practices:**
    - Check for critical dependencies at startup. (Ref: @startup-dependency-check-001.mdc).
    - Provide clear error messages for missing dependencies.
    - Implement graceful degradation for missing optional dependencies.
    - Test with missing dependencies.
    
    ```visual-basic
    # ✅ DO: Gracefully check for and handle missing dependencies
    # def check_and_use_optional_dependency(feature_name, module_name, install_hint=""): # AI adapts
    # ... (full example from previous version) ...
    
    # ❌ DON'T: Assume dependencies exist
    ```
    
    
    

### D. Code Protection Systems & Methodologies

*(AI should aim to build resilient code by applying these principles during fix implementation.)*

1. **Invariant Preservation System:**
    - **Function Contracts (Pre/Post-conditions, Invariants):** Define and document clear contracts. Use assertions for validation. (Ref: @function-contract-assertion-generation-001.mdc).
        
        ```visual-basic
        # ✅ DO: Define and check invariants and contracts
        # def process_playlist_with_contracts(url: str, output_dir: str, **options): # AI adapts
        # ... (full example from previous version) ...
        
        # ❌ DON'T: Leave contracts implicit and unchecked.
        ```
        
        
        
    - **State Machine Protection:** For complex objects, define valid states/transitions and implement runtime validation.
2. **Atomic and Reversible Changes:**
    - **Change Isolation:** Implement fixes as small, isolated, testable units. (Ref: @commit-atomicity-principle-001.mdc).
    - Consider feature flags for significant fixes.
    - **Shim Layer Protection (Advanced):** For high-risk changes, consider a "shim" layer.
        
        ```visual-basic
        # ✅ DO: Example of a conceptual protective shim
        # def safe_critical_function_shim(*args, **kwargs): # AI adapts
        # ... (full example from previous version) ...
        
        # ❌ DON'T: Directly modify highly complex functions without safeguards.
        ```
        
        
        
3. **Patch Implementation Guidelines:** (Ref: @patch-implementation-guidelines-001.mdc)
    - **Containment Strategy:** Limit scope of fixes. Avoid changing public interfaces. Document assumptions.
    - **Defensive Code Modification Patterns:** Prefer adding validation, make functions tolerant, favor gradual deprecation.
        
        ```visual-basic
        # ✅ DO: Use defensive programming when patching
        # def patched_process_data_defensively(data_input): # AI adapts
        # ... (full example from previous version) ...
        
        # ❌ DON'T: Introduce breaking changes in a patch without handling old cases.
        ```
        
        
        

### E. Comprehensive Testing and Validation (Post-Fix)

*(AI must ensure fixes are thoroughly validated.)*

1. **Exhaustive Verification Strategy:**
    - **Comprehensive Edge Case Re-evaluation:** Re-test edge cases around the fix. (Ref: @edge-case-test-creation-and-documentation-001.mdc).
        
        ```visual-basic
        # ✅ DO: Systematically identify and re-test edge cases after a fix.
        # Example: Post-fix, AI re-tests 'process_playlist' with edge cases for 'output_dir': None, "", "non_existent_path/", "/root/protected_dir"
        
        # ❌ DON'T: Only test the specific scenario that initially revealed the bug.
        ```
        
        
        
    - **Cross-Platform Verification (If Applicable).**
2. **Patch Testing Requirements:**
    - Create specific automated test cases reproducing the original bug. (Ref: @automated-test-requirements-001.mdc).
    - Verify fix on all supported platforms if environment-sensitive.
    - Test boundary conditions related to the fix.
    - Ensure no performance degradation. (Ref: @performance-test-requirements-001.mdc).
3. **Integration Testing Framework:**
    - Run full regression test suite. (Ref: @regression-testing-execution-001.mdc).

### F. Debugging Infrastructure Enhancement (Post-Fix)

*(AI should consider if the debugging process revealed needs for better infrastructure.)*

1. **Enhanced Logging (Iterative Improvement):** Add/improve logging around fixed area. (Ref: @enhanced-logging-practices-001.mdc).
    
    ```visual-basic
    # ✅ DO: Add context-rich logging around a fixed area
    # def fixed_function(param_a, param_b): # AI adapts
    # ... (full example from previous version) ...
    
    # ❌ DON'T: Leave complex fixed areas with sparse logging.
    ```
    
    
    
2. **State Inspection Probes (If Useful):** Add debug points/logging to inspect state.

### G. Documentation and Knowledge Management (Post-Fix)

*(AI must ensure learnings from the bug and fix are captured.)*

1. **Bug Fix Documentation:** Utilize a structured template. (Ref: @bugfix-documentation-standard-001.mdc).
    - **Example Fix Documentation Template (for AI to use and populate):**
        
        ```visual-basic
        ## Bug Fix: [Short, Descriptive Title of Bug Fixed]
        
        **Issue Reference:** #[Issue_Tracker_ID] | Commit: [Relevant_Commit_SHA_PreFix]
        
        **Problem Description:** ...
        **Root Cause Analysis:** ... (Ref: @root-cause-causality-chain-documentation-001.mdc if chain documented)
        **Solution Implemented:** ...
        **Validation & Testing:** ... (Ref: @validation-evidence-documentation-001.mdc)
        ... (other fields from previous template) ...
        ```
        
        **content_copydownload**Use code [**with caution**](https://support.google.com/legal/answer/13505487).Markdown
        
    - **Code Comment Requirements (around the fix):** Explain the "why," reference issues.
2. **Knowledge Transfer System (Post-Fix Documentation):**
    - **Bug-Driven Documentation Updates:** Update any project documentation made unclear by the bug. (Ref: @technical-doc-update-milestones-001.mdc, @component-readme-content-standard-001.mdc).
    - **Code Annotation Protocol (around the fix):** Add insightful comments. (Ref: @code-annotation-best-practices-001.mdc).
        
        ```visual-basic
        # ✅ DO: Annotate fixed code with debugging insights and history
        # def get_user_settings(user_id: str) -> dict: # AI adapts
            # INVARIANT: user_id is assumed validated.
            # HISTORY: Fix for Issue #77 - Previously crashed if None.
            # ASSUMPTION: Default settings are always present.
            # WARNING: Perf implications on cache miss.
            # ...
        
        # ❌ DON'T: Leave complex fixes or assumptions undocumented.
        ```
        
        
        

### H. Meta-Debugging System (AI Self-Reflection & Process Improvement)

*(AI should use this to reflect on its own debugging process and ensure rigor.)*

1. **Meta-Debugging Protocol:**
    - **Fix Verification Checklist (AI Internal Check):** Before marking a bug fix "Validated," AI internally verifies against a checklist (incorporating relevant rule IDs):
        
        ```visual-basic
        ### AI Internal Fix Verification Checklist:
        - [ ] 1. Root cause documented (Ref: @root-cause-causality-chain-documentation-001.mdc or similar)?
        - [ ] 2. Affected code paths considered?
        - [ ] 3. Fix addresses documented root cause?
        - [ ] 4. Edge cases tested (Ref: @edge-case-test-creation-and-documentation-001.mdc)?
        - [ ] 5. Contracts/invariants maintained (Ref: @function-contract-assertion-generation-001.mdc)?
        - [ ] 6. Regression tests passed (Ref: @regression-testing-execution-001.mdc)?
        - [ ] 7. Performance not degraded (Ref: @performance-test-requirements-001.mdc)?
        - [ ] 8. Fix aligns with architecture & standards (Ref: @code-quality-..., etc.)?
        - [ ] 9. Error handling/logging enhanced (Ref: @enhanced-logging-practices-001.mdc)?
        - [ ] 10. (Advanced) Failure prediction considered?
        ```
        
        **content_copydownload**Use code [**with caution**](https://support.google.com/legal/answer/13505487).Markdown
        
    - **Debugging Journal (AI Internal Log):** For complex debugging, AI maintains an internal log.
2. **Cross-Cutting Concerns (Reinforced During Debugging):**
    - **API Parameter Validation (Reinforce):** Ensure fix includes robust entry-point validation. (Ref: @api-parameter-validation-at-entry-001.mdc).
        
        ```visual-basic
        # ✅ DO: Example of adding robust parameter validation during a fix
        # def fixed_process_playlist(self, url: str, output_dir, **options): # AI adapts
        #    # --- Parameter Validation Block (added as part of a fix) ---
        #    if not isinstance(url, str) or not url.startswith("https://open.spotify.com/playlist/"):
        #        raise ValueError(f"Invalid Spotify playlist URL: {url}")
        #    # ... more validation ...
        #    # --- End Parameter Validation Block ---
        #    # ... proceed ...
        
        # ❌ DON'T: Assume parameters passed between internal functions are always valid.
        ```
        
        
        
    - **Error Type Consistency (Reinforce):** Ensure fix uses specific, hierarchical error types. (Ref: @consistent-error-typing-001.mdc).

---

This rule definition file guides the AI Executor (Cursor) in applying a comprehensive and robust debugging methodology. It should be referenced by the AI when encountering errors that require investigation and fixing, ensuring a systematic approach to achieving a "one-shot" (i.e., thorough and lasting) fix.