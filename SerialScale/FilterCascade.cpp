/*
   Copyright 2016 Albertas Mickėnas

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/
#include "FilterCascade.h"

FilterCascade::FilterCascade(unsigned char _size, unsigned char heaviness[]):
  size(_size)
{
  unsigned char i;
  if(size > MAX_CASCADE_SIZE) {
    size = MAX_CASCADE_SIZE;
  }

  for(i = 0; i < size; i++) {
    filters[i].heaviness = heaviness[i];
  }
}

long FilterCascade::filter(struct Filter *filter, long value) {
    filter->filteredVal = filter->filteredVal + ((value - filter->filteredVal) >> filter->heaviness);
    return filter->filteredVal;
}

long FilterCascade::apply(long value) {
    long filtered = value;
    int i = 0;
    for(i = 0; i < size; i++) {
        filtered = filter(&filters[i], filtered);
    }
    return filtered;
}

