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
import re
from pandas import DataFrame

from metadata_flatten.parsers import Flatten


class Parser(Flatten):
    def __init__(self, path_content):
        super().__init__(path_content)

    @staticmethod
    def known_types():
        """Return the output types for this generator
        :return: list.  List of output types (file types) for this generator
        """
        return ['shot']

    def parse(self, run_options):
        """Flatten GCP Shot Change Detection - https://cloud.google.com/video-intelligence/docs/analyze-shots

        :param: run_options (dict): specific runtime information 
        :returns: (DataFrame): DataFrame on successful decoding and export, None (or exception) otherwise
        """
        # read data.json
        #   "annotationResults": [ "shotAnnotations": [ {
        #     "startTimeOffset": "0s",
        #     "endTimeOffset": "19.285933s"
        #   }, ...
        dict_data = self.get_extractor_results("gcp_videointelligence_shot_change", "data.json")
        if not dict_data:  # do we need to load it locally?
            if 'extractor' in run_options:
                path_content = path.join(self.path_content, "data.json")
            else:
                path_content = path.join(self.path_content, "gcp_videointelligence_shot_change", "data.json")
            dict_data = self.json_load(path_content)
            if not dict_data:
                path_content += ".gz"
                dict_data = self.json_load(path_content)

        if "annotationResults" not in dict_data:
            if run_options["verbose"]:
                self.logger.critical(f"Missing nested 'annotationResults' from source 'gcp_videointelligence_shot_change'")
            return None

        re_time_clean = re.compile(r"s$")
        for annotation_obj in dict_data["annotationResults"]:  # traverse items
            if "shotAnnotations" in annotation_obj:  # validate object
                list_items = []
                for shot_item in annotation_obj["shotAnnotations"]:
                    if "startTimeOffset" not in shot_item:
                        self.logger.critical(f"Missing nested 'startTimeOffset' in shot chunk '{shot_item}'")
                        return None
                    list_items.append( {"time_begin": float(re_time_clean.sub('', shot_item["startTimeOffset"])), 
                        "time_end": float(re_time_clean.sub('', shot_item["endTimeOffset"])), 
                        "time_event": float(re_time_clean.sub('', shot_item["startTimeOffset"])), 
                        "source_event": "video", "tag": "shot", "score": 1.0, "details": "", "tag_type": "shot",
                        "extractor": "gcp_videointelligence_shot_change"})
                return DataFrame(list_items)

        if run_options["verbose"]:
            self.logger.critical(f"Missing nested 'shotAnnotations' from source 'gcp_videointelligence_shot_change'")
        return None        