import subprocess

# Path to your shell script
shell_script = "/Users/maximebouthillier/gitmax/code/dr_letourneau/ICH_SEGMENTER_V2/testingmaxime/from_sct_qc.sh"

# Execute the shell script
result = subprocess.run([shell_script], capture_output=True, text=True)

# Print the output and error (if any)
print("stdout:", result.stdout)
print("stderr:", result.stderr)
print("Return code:", result.returncode)
