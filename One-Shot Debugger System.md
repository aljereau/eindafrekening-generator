---
description: 
globs: 
alwaysApply: false
---
# One-Shot Debugging Guarantee System

## Core Debugging Process

- **Error Classification and Investigation**
  - Categorize errors by subsystem (API, file system, threading, UI, dependencies)
  - Extract complete context from error messages and logs
  - Verify error is reproducible before attempting fixes
  - Trace error propagation through call chain to find root cause

- **Five-Phase Debugging Process**
  - **Phase 1: Observation**
    - Capture complete error information including stack traces
    - Document exact steps to reproduce
    - Identify environment variables and state when error occurs
    - Log relevant object states at error time
  
  - **Phase 2: Analysis**
    - Follow error propagation chain back to source
    - Check for similar existing bugs or patterns
    - Distinguish between symptoms and root causes
    - Map affected and potentially affected components
  
  - **Phase 3: Solution Design**
    - Create fix plan with clear scope boundaries
    - Identify all possible side effects
    - Consider layered approach (immediate patch + long-term fix)
    - Prepare validation criteria before implementing
  
  - **Phase 4: Implementation**
    - Apply minimal changes required to fix issue
    - Preserve interface contracts
    - Update logging to assist future debugging
    - Document fix rationale in comments
  
  - **Phase 5: Validation**
    - Verify fix resolves original issue
    - Test edge cases around the fix
    - Conduct regression testing on related components
    - Monitor for unintended consequences

## Advanced Root Cause Analysis

- **Comprehensive Root Cause Analysis**
  - **Falsifiable Hypotheses Testing**
    - Form multiple competing hypotheses about bug causes
    - Design tests that can definitively eliminate incorrect hypotheses
    - Require evidence of root cause, not just correlation
    - Document ruled-out causes to prevent revisiting
  
  - **Layered Causality Chain Mapping**
    ```python
    # ✅ DO: Document the complete causality chain
    # Bug: TypeError in process_playlist
    # Layer 1: playlist_service.py:145 - TypeError when passing dict to process_playlist
    # Layer 2: PlaylistWorker receives dict instead of string path
    # Layer 3: Unchecked parameter type in playlist_service.py:45
    # Layer 4: playlist_input_view.py passes options dict directly
    # ROOT CAUSE: Missing type conversion in playlist_input_view.py:212
    
    # ❌ DON'T: Stop at first error occurrence
    # Bug: TypeError in process_playlist - fixed by adding isinstance check
    ```

- **Formal Change Impact Analysis**
  - **Control Flow Impact Map**
    - Identify all code paths that execute modified code
    - Map upstream and downstream dependencies
    - Document every possible code path affected
    - Create state transition diagrams for critical functions
  
  - **Data Flow Analysis**
    ```python
    # ✅ DO: Document all variable mutations
    # output_dir: 
    #   - Created in playlist_input_view.py:205
    #   - Modified in playlist_service.py:128
    #   - Passed to PlaylistWorker.__init__() at line 150
    #   - Used in process() method at line 60
    #   - Passed to backend process_playlist() at line 75
    
    # ❌ DON'T: Assume variables maintain type consistency
    # output_dir is a string
    ```

## Error Category-Specific Guidelines

- **File System Errors**
  ```python
  # ✅ DO: Handle platform-specific paths with protection
  def normalize_path(path):
      if not isinstance(path, (str, bytes, os.PathLike)):
          logger.error(f"Invalid path type: {type(path)}")
          return os.path.abspath("output")  # Safe fallback
      return os.path.abspath(path)
  
  # ❌ DON'T: Make assumptions about path format
  def normalize_path(path):
      return path.replace('/', '\\')  # Breaks on non-string paths
  ```
  - Always check path types before operations
  - Use try/except around file operations with specific error handling
  - Verify library dependencies (e.g., pywin32) before file operations
  - Test with invalid paths, long paths, and special characters

- **API Integration Errors**
  ```python
  # ✅ DO: Implement proper API error handling with retries
  def get_playlist_data(playlist_id):
      max_retries = 3
      for attempt in range(max_retries):
          try:
              return sp_client.playlist(playlist_id)
          except spotipy.SpotifyException as e:
              if e.http_status == 429 and attempt < max_retries - 1:
                  time.sleep(2 ** attempt)  # Exponential backoff
                  continue
              raise SpotifyExtractorError(f"API error: {str(e)}", "api_error", e)
  
  # ❌ DON'T: Catch all exceptions without specific handling
  def get_playlist_data(playlist_id):
      try:
          return sp_client.playlist(playlist_id)
      except Exception as e:
          logger.error(f"Error: {e}")
          return {}  # Silent failure with empty data
  ```
  - Implement proper retry mechanisms for transient errors
  - Handle rate limiting gracefully
  - Validate all API responses before use
  - Test with mocked API failures

- **Threading/Concurrency Issues**
  ```python
  # ✅ DO: Properly clean up threads and handle signals
  def cancel_processing(self):
      if self.thread is not None and self.thread.isRunning():
          # Signal the worker to terminate gracefully
          if hasattr(self.worker, 'cancel_requested'):
              self.worker.cancel_requested = True
          # Set a timeout for thread termination
          if not self.thread.wait(5000):  # 5 second timeout
              logger.warning("Thread did not terminate, forcing quit")
              self.thread.terminate()
  
  # ❌ DON'T: Leave threads hanging
  def cancel_processing(self):
      self.thread.quit()  # No wait or cleanup
  ```
  - Always clean up threads properly on application exit
  - Use signals/slots for thread communication
  - Implement timeout handling for long-running operations
  - Test with forced cancellation and interruptions

- **UI/Error Propagation**
  ```python
  # ✅ DO: Handle UI errors with user-friendly messages
  def show_error(self, error):
      if isinstance(error, SpotifyExtractorError):
          msg = f"{error.error_type.capitalize()}: {error.message}"
          self.error_dialog.setDetailedText(str(error.original_error) if error.original_error else "")
      else:
          msg = f"Unexpected error: {str(error)}"
      self.error_dialog.setText(msg)
      self.error_dialog.show()
  
  # ❌ DON'T: Allow unhandled exceptions in UI code
  def process_button_clicked(self):
      self.process_playlist(self.url_input.text())  # No error handling
  ```
  - Implement consistent error handling across all UI components
  - Provide user-friendly error messages with actionable steps
  - Use proper error propagation through signal/slot system
  - Test UI with simulated errors of each type

- **Dependency Management**
  ```python
  # ✅ DO: Gracefully handle missing dependencies
  def check_dependency(name, import_name=None):
      import_name = import_name or name
      try:
          __import__(import_name)
          return True
      except ImportError:
          logger.error(f"Required dependency '{name}' is missing. "
                      f"Please install with: pip install {name}")
          return False
  
  # ❌ DON'T: Assume dependencies exist
  def process_audio():
      import ffmpeg  # Crashes if not installed
  ```
  - Check for all required dependencies at startup
  - Provide clear installation instructions for missing dependencies
  - Implement optional feature paths for non-critical dependencies
  - Test with deliberately missing dependencies

## Code Protection Systems

- **Invariant Preservation System**
  - **Function Contracts**
    ```python
    # ✅ DO: Define and check invariants
    def process_playlist(self, url, output_dir, **options):
        """Process a playlist.
        
        Invariants:
          - PRE: url must be a non-empty string
          - PRE: output_dir must be a string path or a dict with output_dir key
          - POST: return value is always a tuple of (folder_path, tracks_file, links_file)
          - MAINTAIN: self.worker.output_dir is always string, never None
        """
        assert isinstance(url, str) and url, "URL must be a non-empty string"
        # Implementation with contract validation
    
    # ❌ DON'T: Leave contracts implicit
    def process_playlist(self, url, output_dir, **options):
        # No clear documentation of requirements or guarantees
    ```
  
  - **State Machine Protection**
    - Define valid state transitions for objects
    - Verify state consistency after operations
    - Prevent impossible state combinations
    - Implement runtime state validation

- **Atomic and Reversible Changes**
  - **Change Isolation System**
    - Implement changes as isolated, testable units
    - Develop feature flags to toggle fix behavior
    - Create A/B comparison for old vs. new behavior
    - Support rolling back individual changes
  
  - **Shim Layer Protection**
    ```python
    # ✅ DO: Create protective shims around changes
    original_func = module.process_playlist
    
    def safe_process_playlist(*args, **kwargs):
        try:
            # Apply input normalization
            normalized_args = normalize_args(args)
            result = original_func(*normalized_args, **kwargs)
            # Verify result meets expectations
            validate_result(result)
            return result
        except Exception as e:
            logger.error(f"Error in process_playlist: {e}")
            # Optionally fall back to old implementation
            if config.get('enable_fallback'):
                return fallback_implementation(*args, **kwargs)
            raise
    
    # Replace with safe version
    module.process_playlist = safe_process_playlist
    
    # ❌ DON'T: Directly modify complex functions
    # Replacing function body with new implementation
    ```

- **Patch Implementation Guidelines**
  - **Containment Strategy**
    - Limit scope of changes to affected component
    - Avoid changing interfaces unless absolutely necessary
    - Document all assumptions made during patching
    - Consider compatibility with both older and newer code
  
  - **Code Modification Patterns**
    ```python
    # ✅ DO: Use defensive programming
    def process_data(data):
        # Add type checking to existing function
        if not isinstance(data, dict):
            logger.warning(f"Expected dict, got {type(data)}. Converting.")
            data = {"value": data} if data is not None else {}
        return original_process_data(data)
    
    # ❌ DON'T: Break existing behavior
    def process_data(data):
        # Changing parameter expectations without handling old cases
        return original_process_data(data["new_required_field"])
    ```
    - Prefer adding validation over changing function behavior
    - Make functions more tolerant of input variations
    - Favor gradual deprecation over immediate removal
    - Test with both old and new calling patterns

## Comprehensive Testing and Validation

- **Exhaustive Verification Strategy**
  - **Mutation Testing**
    - Deliberately introduce bugs to verify tests catch them
    - Measure test effectiveness by mutation survival rate
    - Identify untested edge cases through mutations
    - Focus fixes on areas with poor mutation test coverage
  
  - **Comprehensive Edge Case Identification**
    ```python
    # ✅ DO: Systematically identify edge cases
    # Function: process_playlist(url, output_dir, include_artist=False)
    # Edge cases:
    # - url: None, empty string, invalid format, non-ASCII, extremely long
    # - output_dir: None, non-string, dict, relative path, absolute path, 
    #               network path, non-existent, read-only, root dir
    # - include_artist: None, non-boolean values
    # - Environment: offline, API rate limited, disk full, permissions issue
    
    # ❌ DON'T: Test only the happy path
    # Test with a valid URL and output directory
    ```
  
  - **Cross-Platform Verification Matrix**
    - Test across all supported OS platforms
    - Verify on all Python versions
    - Check with different dependency versions
    - Create verification checklist for each platform

- **Patch Testing Requirements**
  - Create test cases covering the specific bug scenario
  - Verify fix works on all supported platforms
  - Test with boundary conditions and edge cases
  - Ensure no performance degradation

- **Integration Testing Framework**
  - **Test Case Design Principles**
    - Test each fixed bug with specific test case
    - Include edge cases around fixed functionality
    - Test error handling paths, not just happy paths
    - Verify proper cleanup on error conditions
  
  - **Regression Test Suite**
    - Create automated tests for fixed bugs
    - Run the full test suite before and after changes
    - Monitor performance metrics during testing
    - Test across supported platforms and configurations

## Debugging Infrastructure

- **Enhanced Logging**
  ```python
  # ✅ DO: Add context-rich logging
  def process_playlist(url, output_dir):
      logger.info(f"Processing playlist: {url}")
      logger.debug(f"Output directory: {output_dir} (type: {type(output_dir)})")
      try:
          # Processing code
      except Exception as e:
          logger.error(f"Error processing playlist: {str(e)}", exc_info=True)
          raise
  
  # ❌ DON'T: Use generic log messages
  def process_playlist(url, output_dir):
      logger.info("Processing started")  # Lacks context
      # Processing code
  ```
  - Log parameter values and types at function entry points
  - Include context information in error logs
  - Use appropriate log levels (debug, info, warning, error)
  - Review logs for patterns before making changes

- **State Inspection**
  - Add debug points to inspect object state
  - Verify assumptions about parameter values
  - Check thread states during asynchronous operations
  - Monitor resource usage during long-running tasks

- **Failure Prediction System**
  - **Fault Tree Analysis**
    - Map all possible failure modes
    - Calculate probability of each failure path
    - Identify single points of failure
    - Implement mitigations for likely failures
  
  - **Chaos Engineering for UI**
    - Deliberately inject failures to test resilience
    - Simulate network errors, API failures
    - Test with invalid or corrupt data
    - Verify graceful degradation

## Documentation and Knowledge Management

- **Bug Fix Documentation**
  - **Fix Documentation Template**
    ```
    ## Bug Fix: [Short Description]
    
    **Issue:**
    - Description of the problem
    - Error message or logs
    - Steps to reproduce
    
    **Root Cause:**
    - What was causing the issue
    - Why it was happening
    
    **Solution:**
    - Changes made to fix the issue
    - Why this approach was chosen
    
    **Validation:**
    - How the fix was tested
    - Edge cases considered
    ```
  
  - **Code Comment Requirements**
    - Explain the "why" not just the "what"
    - Reference issue numbers or error messages
    - Document any workarounds or future improvements
    - Note potential edge cases

- **Temporal and Historical Analysis**
  - **Code Archaelogy**
    - Review all historical changes to buggy code
    - Identify when bug was introduced
    - Find similar patterns elsewhere in codebase
    - Understand original design intent
  
  - **Bug Pattern Recognition**
    - Catalog common bug patterns (type mismatch, null handling, etc.)
    - Scan entire codebase for similar patterns
    - Create prevention system for each pattern
    - Implement automated checks for these patterns

- **Knowledge Transfer System**
  - **Bug-Driven Documentation**
    - Update documentation based on bugs found
    - Document non-obvious constraints and invariants
    - Create "gotchas" section for each component
    - Turn bugs into learning opportunities
  
  - **Code Annotation Protocol**
    ```python
    # ✅ DO: Annotate code with debugging insights
    # INVARIANT: output_dir must be string by this point
    # HISTORY: Fixed issue #42 where dict was passed instead of string
    # ASSUMPTION: API response contains 'tracks' key
    # WARNING: Function fails silently if API unavailable
    
    # ❌ DON'T: Leave tribal knowledge undocumented
    # Added this check to fix the bug
    ```

## Meta-Debugging System

- **Meta-Debugging Protocol**
  - **Fix Verification Checklist**
    ```
    □ 1. Root cause fully understood and documented
    □ 2. All affected code paths identified
    □ 3. Fix addresses root cause, not just symptoms
    □ 4. All edge cases tested
    □ 5. No invariants violated
    □ 6. No regression in related functionality
    □ 7. No performance degradation
    □ 8. Fix is consistent with overall architecture
    □ 9. Error handling enhanced for future prevention
    □ 10. Changes reviewed with failure prediction system
    ```
  
  - **Debugging Journal**
    - Document all debugging steps and decisions
    - Record hypotheses tested and eliminated
    - Maintain traceability from symptoms to fixes
    - Enable reproducible debugging process

- **Cross-Cutting Concerns**
  - **API Parameter Validation**
    ```python
    # ✅ DO: Validate parameters early
    def process_playlist(self, url, output_dir, **options):
        # Validate and normalize parameters
        if not url or not isinstance(url, str):
            raise ValueError(f"Invalid URL: {url}")
        
        if isinstance(output_dir, dict):
            # Extract from dictionary if needed
            actual_output_dir = output_dir.get("output_dir", "output")
        else:
            actual_output_dir = output_dir if isinstance(output_dir, str) else "output"
        
        # Proceed with validated parameters
    
    # ❌ DON'T: Assume parameter validity
    def process_playlist(self, url, output_dir, **options):
        # Directly use parameters without validation
        folder_path = os.path.join(output_dir, "playlist")  # Crashes if output_dir is not a string
    ```
    - Validate and normalize parameters at function entry points
    - Document parameter assumptions in function docstrings
    - Provide clear error messages for invalid parameters
    - Consider adding type hints to clarify expectations
  
  - **Error Type Consistency**
    - Use specific error types for different error categories
    - Include context information in error messages
    - Maintain error hierarchies for proper exception handling
    - Consider providing remediation steps in error messages
