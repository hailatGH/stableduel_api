/**
 * @description Parse data from text content of element with id `element_id`
 * @param {string} element_id
 * @returns {string | null}
 */
export function parseDataFromElement(element_id) {
  const element = document.querySelector(`#${element_id}`);
  if (element !== null) {
    const content = element.textContent;
    const data = JSON.parse(content.replaceAll("'", '"'));
    return data;
  }
  return null;
}
