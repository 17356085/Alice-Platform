<tool_call>
<function=task>
<parameter=description>Explore workflow module structure</parameter>
<parameter=prompt>I need to analyze the workflow module in this project, specifically focusing on the approval-chain page. 

Please do the following:
1. Find all route configuration files in the project (look for files like routes.ts, router.ts, or similar patterns)
2. Find all files related to "workflow" module - search for directories and files containing "workflow" in their path
3. Find all files related to "approval-chain" or "approvalchain" or "approval_chain" 
4. Read the MODULE_CONTEXT.md file if it exists at the project root or any relevant location
5. Look for any layout files related to workflow module

Return:
- The full route configuration for the workflow module
- All page files found in the workflow module
- The directory structure of the workflow module
- Any layout or component files used by approval-chain page
- The content of MODULE_CONTEXT.md if found

Be thorough and search across the entire codebase.</parameter>
<parameter=subagent_type>explore</parameter>
</function>
</tool_call>