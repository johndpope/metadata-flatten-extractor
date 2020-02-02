#! python
# ===============LICENSE_START=======================================================
# vinyl-tools Apache-2.0
# ===================================================================================
# Copyright (C) 2017-2020 AT&T Intellectual Property. All rights reserved.
# ===================================================================================
# This software file is distributed by AT&T 
# under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============LICENSE_END=========================================================
# -*- coding: utf-8 -*-

# Imports
import streamlit as st
import pandas as pd
import numpy as np
import ast
from os import path
from pathlib import Path
import re
import hashlib
import glob
import math
import json

import altair as alt

version_path = path.join("..", "_version.py")
re_issue = re.compile(r"[^0-9A-Za-z]+")
presence_bars = False  # toggle to show presence indicators as a graph

import logging
import warnings
from sys import stdout as STDOUT

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
NLP_TOKENIZE = True
TOP_HISTOGRAM_N = 15
TOP_LINE_N = 5
NLP_FILTER = 0.025
SAMPLE_N = 250

def main_page(data_dir=None, media_file=None):
    """Main page for execution"""
    # read in version information
    version_dict = {}
    with open(version_path) as file:
        exec(file.read(), version_dict)

    st.title(version_dict['__description__']+" Explorer")
    ux_report = st.empty()
    ux_progress = st.empty()

    if data_dir is None:
        data_dir = path.join(path.dirname(version_path), "results")
    if media_file is None:
        media_file = path.join(data_dir, "videohd.mp4")

    df = data_load("data_bundle", data_dir, True)
    if df is None:
        st.error("No data could be loaded, please check configuration options.")
        return
    df_live = draw_sidebar(df)

    # Create the runtime info
    st.markdown(f"""<div style="text-align:left; font-size:small; color:#a1a1a1; width=100%;">
                     <span >{version_dict['__package__']} (v {version_dict['__version__']})</span>
                     <span > - {len(df_live)} events</span></div>""", unsafe_allow_html=True)
    if len(df_live) < SAMPLE_N:
        st.markdown("## Too few samples")
        st.markdown("The specified filter criterion are too rigid. Please modify your exploration and try again.")
        return

    # logger.info(list(df.columns))

    def _aggregate_tags(df_live, tag_type, field_group="tag"):
        df_sub = df_live[df_live["tag_type"]==tag_type].groupby(field_group)["score"] \
                    .agg(['count', 'mean', 'max', 'min']).reset_index(drop=False) \
                    .sort_values(["count", "mean"], ascending=False)
        df_sub[["mean", "min", "max"]] = df_sub[["mean", "min", "max"]].apply(lambda x: round(x, 3))
        return df_sub

    def _quick_sorted_barchart(df_sub):
        """Create bar chart (e.g. histogram) with no axis sorting..."""
        if False:   #  https://github.com/streamlit/streamlit/issues/385
            st.bar_chart(df_sub["tag"].head(TOP_HISTOGRAM_N))
        else:
            # https://github.com/streamlit/streamlit/blob/5e8e0ec1b46ac0b322dc48d27494be674ad238fa/lib/streamlit/DeltaGenerator.py
            st.write(alt.Chart(df_sub.head(TOP_HISTOGRAM_N)).mark_bar().encode(
                x=alt.X('count', sort=None),
                y=alt.Y('tag', sort=None),
                tooltip=['tag', 'count', 'mean', 'min']
            ))


    def quick_hist(df_live, tag_type, show_hist=True):
        """Helper function to draw aggregate histograms of tags"""
        df_sub = _aggregate_tags(df_live, tag_type)
        if len(df_sub) == 0:
            st.markdown("*Sorry, the active filters removed all events for this display.*")
            return None
        # unfortunately, a bug currently overrides sort order
        if show_hist:
            _quick_sorted_barchart(df_sub)
        return df_sub

    def quick_timeseries(df_live, df_sub, tag_type, use_line=True):
        """Helper function to draw a timeseries for a few top selected tags..."""
        if df_sub is None:
            return
        add_tag = st.selectbox("Additional Timeline Tag", list(df_live[df_live["tag_type"]==tag_type]["tag"].unique()))
        tag_top = list(df_sub["tag"].head(TOP_LINE_N)) + [add_tag]

        df_sub = df_live[(df_live["tag_type"]==tag_type) & (df_live["tag"].isin(tag_top))]    # filter top
        df_sub = df_sub[["tag", "score"]]   # select only score and tag name
        df_sub.index = df_sub.index.round('1T')
        list_resampled = [df_sub[df_sub["tag"] == n].resample('1T', base=0).mean()["score"] for n in tag_top]   # resample each top tag
        df_scored = pd.concat(list_resampled, axis=1).fillna(0)
        df_scored.columns = tag_top
        df_scored.index = df_scored.index.seconds // 60
        if use_line:
            st.line_chart(df_scored)
        else:
            st.area_chart(df_scored)

    # frequency bar chart for found labels / tags
    st.markdown("### popular visual tags")
    df_sub = quick_hist(df_live, "tag")  # quick tag hist
    quick_timeseries(df_live, df_sub, "tag")      # time chart of top N 

    # frequency bar chart for types of faces

    # frequency bar chart for keywords
    st.markdown("### popular textual keywords")
    df_sub = _aggregate_tags(df_live, "word", "details")
    if not NLP_TOKENIZE or len(df_sub) < 5:   # old method before NLP stop word removal
        df_sub = _aggregate_tags(df_live, "word", "tag")
        df_sub = df_sub.iloc[math.floor(len(df_sub) * NLP_FILTER):]
        num_clip = list(df_sub["count"])[0]
        st.markdown(f"*Note: The top {round(NLP_FILTER * 100, 1)}% of most frequent events (more than {num_clip} instances) have been dropped.*")
    else:
        st.markdown(f"*Note: Results after stop word removal.*")
        df_sub.rename({"details":"tag"})
    _quick_sorted_barchart(df_sub)

    # frequency bar chart for found labels / tags
    st.markdown("### popular textual named entities")
    df_sub = quick_hist(df_live, "entity")  # quick tag hist

    # frequency bar chart for logos
    st.markdown("### popular logos")
    df_sub = quick_hist(df_live, "logo")
    quick_timeseries(df_live, df_sub, "logo", False)      # time chart of top N 

    # frequency bar chart for emotions

    # frequency bar chart for celebrities
    st.markdown("### popular celebrities")
    df_sub = quick_hist(df_live, "identity")
    quick_timeseries(df_live, df_sub, "identity", False)      # time chart of top N 
    
    # frequency bar chart for celebrities
    st.markdown("### explicit events timeline")
    df_sub = quick_hist(df_live, "explicit", False)
    quick_timeseries(df_live, df_sub, "explicit", False)      # time chart of top N 
    
    # plunk down a dataframe for people to explore as they want
    st.markdown(f"### filtered exploration ({SAMPLE_N} events)")
    filter_tag = st.selectbox("Tag Type for Exploration", ["All"] + list(df_live["tag_type"].unique()))
    order_tag = st.selectbox("Sort Metric", ["random", "score - descending", "score - ascending", "time_begin", "time_end", 
                                         "duration - ascending", "duration - descending"])
    order_ascend = order_tag.split('-')[-1].strip() == "ascending"  # eval to true/false
    order_sort = order_tag.split('-')[0].strip()
    df_sub = df_live
    if filter_tag != "All":
        df_sub = df_live[df_live["tag_type"]==filter_tag]
    if order_tag == "random":
        df_sub = df_sub.sample(SAMPLE_N)
    else:
        df_sub = df_sub.sort_values(order_sort, ascending=order_ascend).head(SAMPLE_N)
    st.write(df_sub)


@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def data_load(stem_datafile, data_dir, allow_cache=True):
    """Because of repetitive loads in streamlit, a method to read/save cache data according to modify time."""

    # generate a checksum of the input files
    m = hashlib.md5()
    list_files = []
    for filepath in Path(data_dir).rglob(f'*.csv*'):
        list_files.append(filepath)
        m.update(str(filepath.stat().st_mtime).encode())
    if not list_files:
        logger.critical(f"Sorry, no flattened files found, check '{data_dir}'...")
        return None 

    # NOTE: according to this article, we should use 'feather' but it has depedencies, so we use pickle
    # https://towardsdatascience.com/the-best-format-to-save-pandas-data-414dca023e0d
    path_new = path.join(data_dir, f"{stem_datafile}.{m.hexdigest()[:8]}.pkl.gz")
    path_backup = None
    for filepath in Path(data_dir).glob(f'{stem_datafile}.*.pkl.gz'):
        path_backup = filepath
        break

    # see if checksum matches the datafile (plus stem)
    if allow_cache and (path.exists(path_new) or path_backup is not None):
        if path.exists(path_new):  # if so, load old datafile, skip reload
            return pd.read_pickle(path_new)
        else:
            st.warning(f"Warning: Using datafile `{path_backup.name}` with no grounded reference.  Version skew may occur.")
            return pd.read_pickle(path_backup)
    
    # time_init = pd.Timestamp('2010-01-01T00')  # not used any more
    ux_report = st.empty()
    ux_progress = st.empty()
    ux_report.info(f"Data has changed, regenerating core data bundle file {path_new}...")

    # Add a placeholder
    latest_iteration = st.empty()
    ux_progress = st.progress(0)
    task_buffer = 5   # account for time-norm, sorting, shot-mapping, named entity
    task_count = len(list_files)+task_buffer

    df = None
    for task_idx in range(len(list_files)):
        f = list_files[task_idx]
        ux_progress.progress(math.floor(float(task_idx)/task_count*100))
        ux_report.info(f"Loading file '{f.name}'...")
        df_new = pd.read_csv(str(f.resolve()))
        df = df_new if df is None else pd.concat([df, df_new], axis=0, sort=False)
    df["details"].fillna("", inplace=True)

    # default with tag for keywords
    df.loc[df["tag_type"]=="word", "details"] = df[df["tag_type"]=="word"]
    if NLP_TOKENIZE:
        # extract/add NLP tags from transcripts
        ux_report.info(f"... detecting NLP-based textual entities....")
        ux_progress.progress(math.floor(float(task_idx)/task_count*100))
        task_idx += 1
        try:
            import spacy
        except Exception as e:
            logger.critical("Missing `spacy`? Consider installing the library (`pip install spacy`) and data model once more. (e.g. python -m spacy download en_core_web_sm)")
        # models - https://spacy.io/models/en 
        # execute -- python -m spacy download en_core_web_sm
        # https://github.com/explosion/spacy-models/releases/download/en_core_web_md-2.2.5/en_core_web_md-2.2.5.tar.gz
        nlp = spacy.load('en_core_web_sm')
        list_new = []
        df_sub = df[df["tag_type"]=="transcript"]
        idx_sub = 0

        for row_idx, row_transcript in df_sub.iterrows():
            ux_report.info(f"... detecting NLP-based textual entities ({idx_sub}/{len(df_sub)})....")
            # https://spacy.io/usage/linguistic-features#named-entities
            detail_obj = json.loads(row_transcript['details'])
            idx_sub += 1
            if "transcript" in detail_obj:
                for entity in nlp(detail_obj["transcript"]).ents:
                    row_new = row_transcript.to_dict()
                    row_new["details"] = entity.label_
                    row_new["tag"] = entity.text
                    row_new["tag_type"] = "entity"
                    list_new.append(row_new)
        ux_report.info(f"... integrating {len(list_new)} new text entities....")
        df_entity = pd.DataFrame(list_new)
        df = pd.concat([df, df_entity])
        list_new = None
        df_entity = None

        # Create list of word tokens
        ux_report.info(f"... filtering text stop words....")
        ux_progress.progress(math.floor(float(task_idx)/task_count*100))
        task_idx += 1
        # from spacy.lang.en.stop_words import STOP_WORDS
        df_sub = df[df["tag_type"]=="word"]
        list_new = df_sub["details"]
        idx_sub = 0
        re_clean = re.compile(r"[^0-9A-Za-z]")
        for row_idx, row_word in df_sub.iterrows():
            word_new = nlp(row_word["tag"])
            list_new[idx_sub] = re_clean.sub('', word_new.text.lower()) if not nlp.vocab[word_new.text].is_stop else "_stopword_"
            idx_sub += 1
        df.loc[df["tag_type"]=="word", "details"] = list_new

    # extract shot extents
    ux_report.info(f"... mapping shot id to all events....")
    ux_progress.progress(math.floor(float(task_idx)/task_count*100))
    task_idx += 1
    df["duration"] = df["time_end"] - df["time_begin"]
    df["shot"] = 0
    df_sub = df[df["tag"]=="shot"]
    idx_sub = 0
    for row_idx, row_shot in df_sub.iterrows():
        ux_report.info(f"... mapping shot id to all events ({idx_sub}/{len(df_sub)}) for {len(df)} samples....")
        # idx_match = df.loc[row_shot["time_begin"]:row_shot["time_end"]].index   # find events to update
        idx_match = df.loc[(df["time_begin"] >= row_shot["time_begin"])
                            & (df["time_end"] < row_shot["time_end"])].index   # find events to update
        df.loc[idx_match, "duration"] = row_shot["duration"]
        df.loc[idx_match, "shot"] = idx_sub
        idx_sub += 1

    ux_report.info(f"... normalizing time signatures...")
    ux_progress.progress(math.floor(float(task_idx)/task_count*100))
    task_idx += 1
    for tf in ["time_event", "time_begin", "time_end"]:  # convert to pandas time (for easier sampling)
        if False:
            df[tf] = df[tf].apply(lambda x: pd.Timestamp('2010-01-01T00') + pd.Timedelta(x, 'seconds'))
        else:
            df[tf] = pd.to_timedelta(df[tf], unit='s')
            df[tf].fillna(pd.Timedelta(seconds=0), inplace=True)

    ux_report.info(f"... sorting and indexing....")
    ux_progress.progress(math.floor(float(task_idx)/task_count*100))
    task_idx += 1
    df.sort_values(["time_begin", "time_end"], inplace=True)
    df.set_index("time_event", drop=True, inplace=True)

    # extract faces (emotion)

    ux_report.info(f"... loaded {len(df)} rows across {len(list_files)} files.")
    ux_report.empty()
    ux_progress.empty()

    # save new data file before returning
    df.to_pickle(path_new)
    return df



def draw_sidebar(df, sort_list=None):
    # Generate the slider filters based on the data available in this subset of titles
    # Only show the slider if there is more than one value for that slider, otherwise, don't filter
    st.sidebar.title('Discovery Filters')
    st.sidebar.markdown("<br>", unsafe_allow_html=True)

    # strict timeline slider
    value = (int(df.index.min().seconds // 60), int(df.index.max().seconds // 60))
    time_bound = st.sidebar.slider("Time Range (min)", min_value=value[0], max_value=value[1], value=value)
    st.sidebar.markdown("<br>", unsafe_allow_html=True)

    # extract shot extents (shot length)
    value = (int(df["duration"].min()), int(df["duration"].max()))
    duration_bound = st.sidebar.slider("Shot Duration (sec)", min_value=value[0], max_value=value[1], value=value, step=1)
    st.sidebar.markdown("<br>", unsafe_allow_html=True)

    # confidence measure
    value = (df["score"].min(), df["score"].max())
    score_bound = st.sidebar.slider("Insight Score", min_value=value[0], max_value=value[1], value=value, step=0.01)
    st.sidebar.markdown("<br>", unsafe_allow_html=True)


    # extract faces (emotion)

    # Filter by slider inputs to only show relevant events
    df_filter = df[(df['time_begin'] >= pd.to_timedelta(time_bound[0], unit='min')) 
                    & (df['time_end'] <= pd.to_timedelta(time_bound[1], unit='min'))
                    & (df['duration'] >= duration_bound[0]) 
                    & (df['duration'] <= duration_bound[1])
                    & (df['score'] >= score_bound[0]) 
                    & (df['score'] <= score_bound[1])
    ]


    # hard work done, return the trends!
    if sort_list is None:
        return df_filter
    # otherwise apply sorting right now
    return df_filter.sort_values(by=[v[0] for v in sort_list], 
                                       ascending=[v[1] for v in sort_list])

def main(args=None):
    import argparse
    
    parser = argparse.ArgumentParser(
        description="""A script run the data explorer.""",
        epilog="""Process TBD...
            # specify the input media file 
            streamlit run timed.py -- -m video.mp4
    """, formatter_class=argparse.RawTextHelpFormatter)
    submain = parser.add_argument_group('main execution')
    submain.add_argument('-d', '--data_dir', dest='data_dir', type=str, default='../results', help='specify the source directory for flattened metadata')
    submain.add_argument('-m', '--media_file', dest='media_file', type=str, default='', help='specific media file for extracting clips (empty=no clips)')

    if args is None:
        config_defaults = vars(parser.parse_args())
    else:
        config_defaults = vars(parser.parse_args(args))
    print(f"Runtime Configuration {config_defaults}")

    main_page(**config_defaults)


# main block run by code
if __name__ == '__main__':
    """ Main page for streamlit timed data explorer """
    main()
