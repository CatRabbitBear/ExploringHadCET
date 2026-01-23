### Baselines and anomalies

Throughout this project, temperatures are shown relative to a fixed historical baseline. Anomalies are calculated by comparing observed monthly mean temperatures against the **1960–1991** reference period.

This baseline is widely used in climate reporting and provides a stable point of comparison within the instrumental record. Using a fixed baseline allows values from different centuries to be compared consistently, but it also means that anomalies reflect differences relative to that chosen period rather than absolute temperature values.

No attempt is made here to optimise or adjust the baseline for specific visualisations. The emphasis is on transparency and consistency rather than selecting a reference that highlights particular features of the record.

---

### Smoothing and local regression

Some visualisations in this project apply smoothing across time to reduce visual noise and make broader structure easier to see. Where this is done, it uses **local regression (LOESS)**, a method that fits simple models to local subsets of the data rather than applying a single global trend.

LOESS is well suited to long observational records because it can adapt to local variation without assuming a fixed functional form. At the same time, it has important limitations. The results depend on choices such as the smoothing window, and behaviour near the edges of the record can be less reliable because fewer neighbouring data points are available.

In this project, smoothing is used as a **visual aid only**. It is not intended to replace the underlying measurements or to imply a definitive trend. A general overview of the method is available on [Wikipedia’s Local Regression page](https://en.wikipedia.org/wiki/Local_regression).

---

### Winter grouping and boxplots

The *Winter in Focus* section groups **December, January, and February (DJF)** together. These months are commonly treated as a single winter period because they represent the core of the cold season and share similar underlying dynamics.

Boxplots are used to summarise the distribution of winter temperatures within selected time spans. This representation highlights the spread of values, the typical range, and the presence of more extreme outcomes, while avoiding emphasis on individual years.

It is important to note that boxplots at the most recent end of the record may be **incomplete**. When a time span is still ongoing, the available data can only fill part of the distribution. In these cases, the tails of the boxplot can only extend further as more data becomes available, while the position of the box itself may shift in either direction.

These plots are therefore intended to support comparison between periods, rather than to provide a final or complete summary of recent decades.
