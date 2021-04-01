## FireCam

Data for this section was collected from the [HPWREN](https://hpwren.ucsd.edu/) fire lookout network. Images were collected and tagged by [Open Climate Tech](https://openclimatetech.org/), and published as a supplement to [Govil et al, 2020](https://doi.org/10.3390/rs12010166 "Govil, K.; Welch, M.L.; Ball, J.T.; Pennypacker, C.R. Preliminary Results from a Wildfire Detection System Using Deep Learning on Remote Camera Images. Remote Sens. 2020, 12, 166."). Part of the dataset is archived with the [FireCam project](https://github.com/open-climate-tech/firecam/tree/master/datasets/2019a).

## Data preparation

[Govil et al, 2020](https://doi.org/10.3390/rs12010166 "Govil, K.; Welch, M.L.; Ball, J.T.; Pennypacker, C.R. Preliminary Results from a Wildfire Detection System Using Deep Learning on Remote Camera Images. Remote Sens. 2020, 12, 166.") apply the [InceptionV3](https://www.tensorflow.org/api_docs/python/tf/keras/applications/InceptionV3) architecture as their classification algorithm. InceptionV3 expects image inputs with resolution of 299x299px.

HPWREN cameras use very wide angle lenses, and compressing each 6-megapixel image down to 299x299 would cause unacceptable resolution loss at the scale of smoke plumes, which are frequently in the far distance. The simplest way to handle this is to crop the full size images down into 299x299px segments that can be analyzed independently.

The Govil et al dataset consists of a collection of pre-cropped negative examples containing no smoke, and a set of images that do include early-stage forest fire plumes. They also include a csv file indicating bounding boxes for regions of the full positive images where smoke is present.

Because there are many more negative examples than positive examples, each positive example is sampled multiple times with various offsets (center, upper left, lower left, upper right, lower right), producing 5-fold increase in training examples. All of those examples are also mirrored to produce an overall 10-fold increase in number of training examples.

## Processing

The notebook [firecam.ipynb](./firecam.ipynb) handles the pre-processing steps described above.
It first extracts those cropped/shifted/mirrored segments of the positive training examples, and saves them into a new directory. It then uses the [make_training_data_eplorer.sh](./make_training_data_explorer.sh) script to generate browsable HTML pages for verifying that the preprocessing steps were executed correctly.

The preprocessed data can be viewed in [training/non_smoke.html](./training/non_smoke.html) and [training/smoke_cropped.html](./training/smoke_cropped.html).