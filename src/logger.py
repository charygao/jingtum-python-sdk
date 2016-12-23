
"""
 * Copyright@2016 Jingtum Inc. or its affiliates.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
"""

import logging
import sys
 

def set_logger(level=logging.DEBUG, path=sys.path[0], name="jingtumsdk.log"):
   logger = logging.getLogger() 
   logger.setLevel(level)  
   fh = logging.FileHandler(path + '/' + name)  
   ch = logging.StreamHandler() 

   formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')  
   fh.setFormatter(formatter)  
   ch.setFormatter(formatter)  

   logger.addHandler(fh)  
   logger.addHandler(ch) 

   return logger

logger = set_logger()

