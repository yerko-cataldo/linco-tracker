import pandas as pd
df = pd.read_csv("eval/results/raw.csv").query("task == 'meal'")
df["err"] = df.kcal - df.ref_kcal
print(df.pivot_table(index="case", columns="model", values="err").round(0))