# Recursive 10-Minute EC/pH Forecasting Workflow

## Goal

Build a forecasting system that:

- starts from a **real EC/pH sample**
- predicts **EC and pH every 10 minutes**
- uses the **previous predicted state** as the input state for the next step
- keeps rolling forward until it reaches the **next real sample**
- compares prediction vs. reality at that real sample
- retrains the model **only when a new real sample is encountered**

This is **not** standard one-step supervised learning, and it is also **not exactly direct gap prediction**.

The correct description is:

**Recursive 10-minute forecasting with retraining at real observation points**

---

## Core Idea

At any time `t`, the model holds a current system state:

- `EC_t`
- `pH_t`

If `t` is a real sample time, the state is initialized from the true measurement.

From there, the model predicts forward in **10-minute steps**:

- from `t` to `t+10m`
- then from `t+10m` to `t+20m`
- and so on

Each next step uses:

1. the current state (`EC`, `pH`)
2. climate variables
3. irrigation/fertigation inputs
4. engineered history features

When the rollout reaches the next real sample time, the predicted values are compared to the true values, error is computed, and the training set can be expanded before retraining.

---

## High-Level Workflow

```text
Real sample at t0
    ↓
Initialize state with true EC/pH at t0
    ↓
Build 10-minute features for interval [t0, t0+10)
    ↓
Predict next state at t0+10
    ↓
Use predicted state as current state
    ↓
Repeat every 10 minutes
    ↓
Reach next real sample at t1
    ↓
Compare predicted EC/pH at t1 to true EC/pH at t1
    ↓
Compute error
    ↓
Optionally add this finished segment to training set
    ↓
Retrain model
    ↓
Reset state to true EC/pH at t1
    ↓
Continue to next segment
```

---

## Data Structure Required

You need one master table on a **uniform 10-minute timeline**.

### Each row should represent one 10-minute timestamp

Example columns:

- `timestamp`
- climate features:
  - `temp`
  - `rh`
  - `ET0`
  - `soil_temp`
  - `radiation` (optional if useful)
- management / crop interface features:
  - irrigation amount in the step
  - fertilizer amount in the step
  - drainage / leaching / canopy / substrate variables if available
- rolling / history features:
  - irrigation last 1h / 3h / 6h / 24h
  - fertilizer last 1h / 3h / 6h / 24h
  - hours since irrigation
  - hours since fertigation
- time features:
  - hour of day
  - sin/cos hour encoding
  - day/night indicator
- observed targets only where available:
  - `ec_true`
  - `ph_true`
  - `is_real_sample` = 1 if a real measurement exists, else 0

Most rows will **not** have real EC/pH measurements. That is expected.

---

## Segmentation Logic

The dataset should be split into **segments between consecutive real samples**.

Example:

- real sample at `t0`
- next real sample at `t1`

Then the segment is:

- start state = true sample at `t0`
- end evaluation = true sample at `t1`
- internal simulation grid = every 10 minutes between them

So each segment is:

```text
Segment k:
start_time = real_sample_time[k]
end_time   = real_sample_time[k+1]
```

The model rolls recursively from `start_time` until `end_time`.

---

## Model Formulation

Two good options exist.

### Option A: Predict next absolute value
For each step:

- predict `EC_(t+10)`
- predict `pH_(t+10)`

### Option B: Predict state change
For each step:

- predict `delta_ec_10m`
- predict `delta_ph_10m`

Then update:

```text
EC_(t+10) = EC_t + delta_ec_pred
pH_(t+10) = pH_t + delta_ph_pred
```

### Recommended
Use **delta prediction** first.

Reason:
- usually more stable
- easier to learn short-term transitions
- reduces level drift compared to direct absolute prediction

---

## Inputs at Each 10-Minute Step

At time `t`, the model should only use information available up to the next step.

### Current state features
- `ec_current`
- `ph_current`

### Step inputs for interval `[t, t+10m)`
- irrigation amount during the interval
- fertilizer amount during the interval
- climate conditions during the interval
- ET0 for the interval
- temperature / RH / soil temperature for the interval

### Historical features known at time `t`
- irrigation total last 1h / 3h / 6h / 24h
- fertilizer total last 1h / 3h / 6h / 24h
- hours since last irrigation
- hours since last fertilizer
- climate rolling means / sums up to time `t`
- time-of-day features

### Important anti-leakage rule
For the step from `t` to `t+10m`, use only:

- current state at `t`
- known inputs in `[t, t+10m)`
- history up to `t`

Do **not** use anything from after `t+10m`.

---

## Rollout Procedure

For a segment from `t0` to `t1`:

### Step 1: Initialize from true sample
```text
ec_current = ec_true(t0)
ph_current = ph_true(t0)
```

### Step 2: Loop every 10 minutes until `t1`
For each step:

1. build features for the current 10-minute interval
2. predict next state
3. update `ec_current`, `ph_current`
4. store the predicted path

Pseudo-logic:

```text
t = t0

while t < t1:
    X_t = features built from:
          current predicted state at t
          climate and management inputs for [t, t+10)
          historical aggregates up to t

    predict delta_ec_t, delta_ph_t

    ec_next = ec_current + delta_ec_t
    ph_next = ph_current + delta_ph_t

    store prediction for t+10

    ec_current = ec_next
    ph_current = ph_next
    t = t + 10 minutes
```

### Step 3: Evaluate at the next real sample
At `t1`:

- `ec_pred(t1)` vs `ec_true(t1)`
- `ph_pred(t1)` vs `ph_true(t1)`

Example errors:

- absolute error
- squared error
- MAE / RMSE over all segments

---

## Retraining Logic

Retraining should happen **only when a new real sample is reached**.

That means:

- no retraining at every 10-minute step
- no pseudo-labeling from predicted values as if they were true labels

### Correct update cycle
1. train model on available historical segments
2. run recursive rollout on the next unseen segment
3. evaluate at the end real sample
4. add the newly completed segment to the training set
5. retrain
6. continue forward

This is essentially a **walk-forward training and evaluation framework**.

---

## Walk-Forward Framework

Suppose real samples are indexed chronologically:

```text
S0, S1, S2, S3, ..., Sn
```

Each segment is:

- segment 0: `S0 -> S1`
- segment 1: `S1 -> S2`
- segment 2: `S2 -> S3`
- ...

### Walk-forward process

```text
Train on early segments
    ↓
Forecast next segment recursively
    ↓
Evaluate at its ending real sample
    ↓
Add this segment to training history
    ↓
Retrain
    ↓
Forecast next segment
    ↓
Repeat
```

### Example
- initial train segments: first 20 segment pairs
- test segment: segment 21
- after finishing segment 21:
  - include it in training
  - retrain
  - forecast segment 22

This matches your idea exactly.

---

## Why This Is Not Standard Direct Gap Prediction

### Direct gap prediction
A direct gap model predicts the future state at the next real sample using aggregated features over the whole gap.

Example:

```text
(start state at t0, total irrigation between t0 and t1, climate summaries between t0 and t1) -> EC/pH at t1
```

That approach predicts the endpoint directly.

### Your approach
Your approach explicitly simulates the state every 10 minutes:

```text
t0 -> t0+10 -> t0+20 -> ... -> t1
```

So your workflow is better described as:

**recursive state-update forecasting with evaluation and retraining at observation points**

---

## Training Choices

Because you do **not** have true EC/pH labels every 10 minutes, standard supervised training is tricky.

There are three main ways to handle this.

### Option 1: Approximate 10-minute labels
Use interpolation or synthetic labels between real samples.

Problem:
- introduces fake targets
- can teach the model unrealistic dynamics

### Option 2: Train using segment-end loss
Run the model recursively across the whole gap and measure loss only at the next real sample.

This is conceptually the cleanest option for your problem.

### Option 3: Hybrid practical approach
Train a simpler transition model from engineered segment/step approximations, then evaluate using true recursive rollout between real samples.

This is usually the best place to start because it is much easier to implement.

### Recommended practical order
1. build the rollout framework first
2. build a simple delta model
3. evaluate walk-forward across real sample segments
4. only then consider more advanced end-of-segment training

---

## Evaluation Metrics

You should evaluate both:

### Final endpoint accuracy
At each real sample time:
- MAE for EC
- RMSE for EC
- MAE for pH
- RMSE for pH
- R² if stable enough

### Error by gap length
Split evaluation by time distance between real samples:

- 0–12h
- 12–24h
- 24h+

This is important because recursive models usually degrade as horizon length increases.

### Drift analysis
Also track:

- cumulative drift over long gaps
- bias direction:
  - always underpredicting EC?
  - always overpredicting pH?

---

## Key Risks

### 1. Error accumulation
Each wrong step becomes the input for the next step.

Result:
- small errors become large drift

Mitigation:
- predict deltas, not only absolutes
- reset to truth at every real sample
- keep model simple
- use physically meaningful features

### 2. Leakage
The biggest technical risk.

Do not use:
- future climate summaries beyond the current step
- future events not yet available in the simulated step
- features derived from the ending real sample

### 3. Too many features with too few real samples
With around 100 real samples, overfitting is a serious risk.

Mitigation:
- use a small, strong feature set first
- prefer simpler models
- compare against naive baselines

---

## Recommended First Version

### Model
Use two separate models:

- model 1: `delta_ec_10m`
- model 2: `delta_ph_10m`

### Candidate algorithms
Start simple:

- XGBoost
- LightGBM
- Random Forest as baseline
- linear / ridge baseline

Do not start with LSTM unless the simpler framework is already working.

### Initial feature set
Use a compact set:

- current EC
- current pH
- irrigation in step
- fertilizer in step
- irrigation last 1h / 6h / 24h
- fertilizer last 1h / 6h / 24h
- ET0 in step
- temp in step
- RH in step
- soil temp in step
- hours since irrigation
- hours since fertilizer
- hour-of-day cyclical features

---

## Full Operational Workflow

```text
1. Build one 10-minute master table
2. Mark all real EC/pH sample times
3. Split timeline into segments between real samples
4. Choose an initial training window of early segments
5. Train EC and pH transition models
6. For the next unseen segment:
      a. initialize from true start sample
      b. rollout every 10 minutes recursively
      c. stop at the next real sample
      d. compute endpoint error
7. Append completed segment to training history
8. Retrain models
9. Reset state to the true sample at the new observation point
10. Continue until the end of the dataset
11. Summarize performance across all segments
```

---

## Best Short Description for the Project

You can describe the workflow like this:

> We use a recursive state-update forecasting framework for root-zone EC and pH.  
> Starting from each real observed sample, the model predicts the next state every 10 minutes using climate and fertigation inputs.  
> The predicted state is then fed back as the input state for the following step.  
> When the rollout reaches the next real sample, the prediction is compared against the true measured EC and pH, the error is recorded, and the model is retrained using the expanded history.  

---

## Final Recommendation

Yes, your idea is feasible.

But the right implementation is:

- **recursive 10-minute rollout**
- **evaluation only at real sample times**
- **retraining only when a real sample is reached**
- **walk-forward validation**
- **strict leakage prevention**

That is the workflow you should build first.

After this framework works, you can decide whether to improve:

- feature engineering
- retraining frequency
- bias correction
- direct end-of-gap training
- physics-informed constraints
