# Changes

A method to flatten generated JSON data into timed CSV events in support of analytic 
workflows within the [ContentAI Platform](https://www.contentai.io). 

## 0.6

### 0.6.2
* rename `rekognition_face_collection` to `aws_rekognition_face_collection` for consistency

### 0.6.1
* split documentation and changes
* add new `cae_metadata` type of parser
* modify `source_type` of detected faces in `azure_videoindexer` to `face`
* modify to add new `extractors` input for limit to scanning (skips sub-dir check)

### 0.6.0
* adding CI/CD script for [gitlab](https://gitlab.com) 
* validate usage as a flattening service 
* modify `source_type` for `aws_rekognition_video_celebs` to `face`

## 0.5

### 0.5.4
* adding `face_attributes` visualization mode for exploration of face data
* fix face processing to split out to `tag_type` as `face` with richer subtags

### 0.5.3
* add labeling component to application (for video/image inspection) 
* fix shot duration computeation in application (do not overwrite original event duration)
* add text-search for scanning named entities, words from transcript

### 0.5.2
* fix bugs in `gcp_videointelligence_logo_recognition` (timing) and `aws_rekognition_video_faces` (face emotions)
* add new detection of `timing.txt` for integration of multiple results and their potential time offsets
* added `verbose` flag to input of main parser
* rename `rekognition_face_collection` for consistency with other parsers

### 0.5.1
* split app modules into different visualization modes (`overview`, `event_table`, `brand_expansion`)
  * `brand_expansion` uses kNN search to expand from shots with brands to similar shots and returns those brands
  * `event_table` allows specific exploration of identity (e.g. celebrities) and brands witih image/video playback
  * **NOTE** The new application requires `scikit-learn` to perform live indexing of features
* dramatically improved frame targeting (time offset) for event instances (video) in application

### 0.5.0
* split main function into sepearate auto-discovered modules
* add new user collection detection parser `rekognition_face_collection` (custom face collections)

## 0.4

### 0.4.5
* fixes for gcp moderation flattening
* fixes for app rendering (switch most graphs to scatter plot)
* make all charts interactive again
* fix for time zone/browser challenge in rendering

### 0.4.4
* fixes for `azure_videoindexer` parser
* add sentiment and emotion summary
* rework graph generation and add bran/entity search capability

### 0.4.3
* add new `azure_videoindexer` parser
* switch flattened reference from `logo` to `brand`; `explicit` to `moderation`
* add parsing library `pytimeparse` for simpler ingest
* fix bug to delete old data bundle if reference files are available

### 0.4.2
* add new `time_offset` parameter to environment/run configuration
* fix bug for reusing/rewriting existing files
* add output prefix `flatten_` to all generated CSVs to avoid collision with other extractor input

### 0.4.1
* fix docker image for nlp tasks, fix stop word aggregation

### 0.4.0
* adding video playback (and image preview) via inline command-line execution of ffmpeg in application
* create new Dockerfile.app for all-in-one explorer app creation

## 0.3

### 0.3.2
* argument input capabilities for exploration app
* sort histograms in exploration app by count not alphabet

### 0.3.1
* browsing bugfixes for exploration application

### 0.3.0
* added new [streamlit](https://www.streamlit.io/) code for [data explorer interface](app)
  * be sure to install extra packages if using this app and starting from scratch (e.g. new flattened files)
  * if you're working from a cached model, you can also drop it in from a friend


## 0.2

### 0.2.1
* schema change for verb/action consistency `time_start` -> `time_begin`
* add additional row field `tag_type` to describe type of tag (see [generated-insights](#generated-insights))
* add processing type `gcp_videointelligence_logo_recognition`
* allow compression as a requirement/input for generated files (`compressed` as input)


### 0.2.0
* add initial package, requirements, docker image
* add basic readme for usage example
* processes types `gcp_videointelligence_label`, `gcp_videointelligence_shot_change`, `gcp_videointelligence_explicit_content`, `gcp_videointelligence_speech_transcription`, `aws_rekognition_video_content_moderation`, `aws_rekognition_video_celebs`, `aws_rekognition_video_labels`, `aws_rekognition_video_faces`, `aws_rekognition_video_person_tracking`, 


# Future Development

* the remaining known extractors... `pyscenedetect`, `yolo3`, `openpose`
* integration of viewership insights
* creation of sentiment and mood-based insights (which tags most co-occur here?)