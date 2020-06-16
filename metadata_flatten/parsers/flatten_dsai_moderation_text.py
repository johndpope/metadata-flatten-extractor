#! python
# ===============LICENSE_START=======================================================
# metadata-flatten-extractor Apache-2.0
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

from os import path
from pandas import DataFrame
import json

from metadata_flatten.parsers import Flatten

class Parser(Flatten):
    def __init__(self, path_content):
        super().__init__(path_content)
        self.EXTRACTOR = "dsai_moderation_text"
        self.SCORE_THRESHOLD = 0.05

    @staticmethod
    def known_types():
        """Return the output types for this generator
        :return: list.  List of output types (file types) for this generator
        """
        return ['moderation']

    def parse(self, run_options):
        """Flatten moderation score results

        :param: run_options (dict): specific runtime information
        :returns: (DataFrame): DataFrame on successful decoding and export, None (or exception) otherwise
        """
        dict_data = self.get_extractor_results(self.EXTRACTOR, "data.json", is_json=True)
        if not dict_data:
            if run_options["verbose"]:
                self.logger.critical(f"Empty result string for extractor '{self.EXTRACTOR}', aborting")
            return None

        # {
        #     "config": {
        #         "version": "1.0.0",
        #         "extractor": "moderation-text-extractor",
        #         "input": "/work/samples/veep/video.mp4",
        #         "timestamp": "2020-05-29 12:58:31.972617"
        #     },
        #     "results": [
        #         {
        #             "begin": 97.594,
        #             "end": 101.923,
        #             "text": "This gorgeous ****, Gracie, she's wearing a campaign button.",
        #             "scores": {
        #                 "toxic": 0.74207,
        #                 "severe_toxic": 0.00048,
        #                 "obscene": 0.0226,
        #                 "threat": 0.00099,
        #                 "insult": 0.002,
        #                 "identity_hate": 0.00022
        #             },
        #             "source": "speech",
        #             "extractor": "azure_videoindexer"
        #         },

        list_items = []

        if dict_data is None or 'results' not in dict_data or 'config' not in dict_data:
            self.logger.critical(f"Missing nested 'results' from source '{self.EXTRACTOR}'")
            return None
        for local_obj in dict_data["results"]:
            if "scores" in local_obj and "begin" in local_obj:  # validate object
                time_begin = float(local_obj['begin'])
                time_end = float(local_obj['end'])
                for score_name in local_obj['scores']:
                    local_score = local_obj['scores'][score_name]
                    if local_score > self.SCORE_THRESHOLD:
                        list_items.append({"time_begin": time_begin, "source_event": local_obj["source"], "tag_type": "moderation",
                            "time_end": time_end, "time_event": time_begin, "tag": score_name, "score": local_score, 
                            "details": json.dumps({"extractor_source": local_obj["extractor"]}), "extractor": self.EXTRACTOR})

        if len(list_items) > 0:   # return the whole thing as dataframe
            return DataFrame(list_items)

        if run_options["verbose"]:
            self.logger.critical(f"No valid events detected for '{self.EXTRACTOR}'")
        return None